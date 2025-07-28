import asyncio
from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from typing import List, Dict

# --- FastAPI App Initialization ---
app = FastAPI(
    title="HiFiNi Music Search API",
    description="An API to search and scrape music links from HiFiNi.",
    version="1.0.0",
)

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Scraper Configuration ---
USERNAME = os.getenv("HIFINI_USERNAME")
PASSWORD = os.getenv("HIFINI_PASSWORD")
BASE_URL = "https://hifiti.com"

# --- Core Scraping Logic (Async Version) ---
async def search_hifini(keyword: str, quick_mode: bool, limit: int, max_pages: int, excluded_forums: List[str]) -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        results = []
        processed_urls = set()

        try:
            # Step 1: Login
            print("Navigating to login page...")
            await page.goto(f"{BASE_URL}/user-login.htm", timeout=60000)
            await page.fill("input[name='email']", USERNAME)
            await page.fill("input[name='password']", PASSWORD)
            await page.click("button:has-text('登录')")
            await page.wait_for_url(f"{BASE_URL}/", timeout=30000)
            print("Login successful.")

            # Step 2: Search
            print(f"Searching for keyword: {keyword}")
            await page.fill("#searchKeyword", keyword)
            await page.click("button.btn.btn-primary")
            await page.wait_for_load_state("networkidle", timeout=30000)

            # Step 3: Scrape results with pagination
            collected_links = []
            current_page = 1
            page_limit = 100 if quick_mode else max_pages

            while current_page <= page_limit:
                print(f"--- Processing page {current_page} ---")
                await page.wait_for_load_state("networkidle")
                thread_elements = await page.query_selector_all("li.media.thread")

                limit_reached = False
                for item in thread_elements:
                    is_excluded = False
                    for forum_href in excluded_forums:
                        if await item.query_selector(f'a[href="{forum_href}"]'):
                            is_excluded = True
                            break
                    if is_excluded:
                        continue

                    link_element = await item.query_selector("div.subject.break-all > a")
                    if link_element:
                        title = await link_element.inner_text()
                        href = await link_element.get_attribute("href")
                        full_url = f"{BASE_URL}/{href}"
                        if full_url not in processed_urls:
                            collected_links.append({"title": title.strip(), "post_url": full_url})
                            processed_urls.add(full_url)
                            if quick_mode and len(collected_links) >= limit:
                                limit_reached = True
                                break
                
                if limit_reached or not await page.locator("a.page-link:has-text('▶')").count():
                    break
                
                await page.locator("a.page-link:has-text('▶')").click()
                current_page += 1

            # Step 4: Fetch media URLs
            for link_info in collected_links:
                try:
                    await page.goto(link_info['post_url'], timeout=60000, wait_until="domcontentloaded")
                    with page.expect_response(lambda r: r.request.resource_type == "media" or ".mp3" in r.url or ".flac" in r.url, timeout=45000) as response_info:
                        play_button = page.locator(".aplayer-button, .aplayer-dplayer").first
                        if await play_button.is_visible():
                            await play_button.click(timeout=5000)
                    media_response = await response_info.value
                    results.append({"title": link_info['title'], "url": media_response.url})
                except PlaywrightTimeoutError:
                    print(f"Timeout (45s) while waiting for media file on page: {link_info['title']}. Skipping.")
                except Exception as e:
                    print(f"Could not fetch media URL for {link_info['title']}: {e}")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            await browser.close()
        
        return results

# --- API Endpoint Definition ---
@app.get("/")
def read_root():
    return {"status": "ok"}


@app.get("/api/search", response_model=List[Dict])
async def search_endpoint(keyword: str, quick: bool = False, limit: int = 10, pages: int = 3, exclude: str = 'forum-7.htm'):
    """
    Search for music on HiFiNi.

    - **keyword**: The search term (e.g., '周杰伦').
    - **quick**: If `true`, returns after finding `limit` results. Overrides `pages`.
    - **limit**: Number of results to return in quick mode.
    - **pages**: Maximum number of pages to scrape if `quick` is `false`.
    - **exclude**: Comma-separated list of forum hrefs to exclude (e.g., 'forum-7.htm,forum-9.htm').
    """
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword cannot be empty.")

    excluded_forums = [f.strip() for f in exclude.split(',') if f.strip()]

    try:
        search_results = await search_hifini(
            keyword=keyword, 
            quick_mode=quick, 
            limit=limit, 
            max_pages=pages, 
            excluded_forums=excluded_forums
        )
        if not search_results:
            raise HTTPException(status_code=404, detail="No results found.")
        return search_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

# --- Uvicorn Runner ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
