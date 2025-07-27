from playwright.sync_api import sync_playwright
import time
import json

USERNAME = "zhuzhuzhuzhu"
PASSWORD = "CHAOfan0920"
SEARCH_KEYWORD = "周杰伦"
BASE_URL = "https://hifiti.com"

results = []

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Step 1: Login
        page.goto(f"{BASE_URL}/user-login.htm")
        page.fill("input[name='email']", USERNAME)
        page.fill("input[name='password']", PASSWORD)
        page.click("button:has-text('登录')")
        # 等待登录成功并跳转回主页
        page.wait_for_url(f"{BASE_URL}/", timeout=30000)
        print("登录成功，已跳转到主页。")

        # 步骤 2: 直接在当前页面搜索 (不再需要重新跳转)
        print(f"开始在主页搜索关键词: {SEARCH_KEYWORD}")
        page.fill("#searchKeyword", SEARCH_KEYWORD)
        page.click("button.btn.btn-primary")
        page.wait_for_load_state("networkidle")

        # Step 3: Collect all result links
        post_links = page.eval_on_selector_all(
            "a[href^='/thread-']",
            "els => els.map(el => ({ title: el.innerText, href: el.href }))"
        )

        for link in post_links:
            title = link['title']
            href = link['href']
            print(f"Visiting: {title}")
            page.goto(href)
            page.wait_for_timeout(2000)

            # Step 4: Click play button
            try:
                with page.expect_response(lambda r: ".mp3" in r.url or ".flac" in r.url) as response_info:
                    page.click(".aplayer-button")
                media_response = response_info.value
                media_url = media_response.url

                print(f"Found: {media_url}")
                results.append({"title": title, "url": media_url})
            except Exception as e:
                print(f"❌ Failed to get media URL for: {title} - {e}")
            time.sleep(1)

        browser.close()

        # Step 5: Save to file
        with open("music_links.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run()
