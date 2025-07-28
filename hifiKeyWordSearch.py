import time
import json
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

USERNAME = "zhuzhuzhuzhu"
PASSWORD = "CHAOfan0920"
if len(sys.argv) > 1:
    SEARCH_KEYWORD = sys.argv[1]
else:
    SEARCH_KEYWORD = input("请输入您要搜索的关键词: ")
BASE_URL = "https://hifiti.com"
MAX_PAGES = 3  # 设置最大翻页数
QUICK_TEST_MODE = True  # 快速测试模式：True表示只抓10个，False表示按MAX_PAGES抓取
QUICK_TEST_LIMIT = 5   # 快速测试模式下的抓取数量

# 在这里添加不希望抓取的板块链接，例如 'forum-7.htm' 是互助区
EXCLUDED_FORUMS = [
    "forum-7.htm"  # 互助区
]

results = []
processed_urls = set() # 用来存储已经处理过的帖子URL，防止重复抓取

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 步骤 1: 登录
        try:
            print("正在尝试登录...")
            page.goto(f"{BASE_URL}/user-login.htm", timeout=60000)
            page.fill("input[name='email']", USERNAME)
            page.fill("input[name='password']", PASSWORD)
            page.click("button:has-text('登录')")
            page.wait_for_url(f"{BASE_URL}/", timeout=30000)
            print("登录成功，已跳转到主页。")
        except PlaywrightTimeoutError:
            print("登录超时或失败，请检查网络或账号密码。")
            browser.close()
            return
        except Exception as e:
            print(f"登录过程中发生未知错误: {e}")
            browser.close()
            return

        # 步骤 2: 搜索
        try:
            print(f"开始在主页搜索关键词: {SEARCH_KEYWORD}")
            page.fill("#searchKeyword", SEARCH_KEYWORD)
            page.click("button.btn.btn-primary")
            page.wait_for_load_state("networkidle", timeout=30000)
        except Exception as e:
            print(f"搜索失败: {e}")
            browser.close()
            return

        # 步骤 3: 循环翻页并采集帖子链接
        collected_links = []
        current_page = 1
        while current_page <= MAX_PAGES:
            print(f"--- 开始处理第 {current_page} 页 ---")
            page.wait_for_load_state("networkidle")
            
            # 获取当前页面的所有帖子
            thread_elements = page.query_selector_all("li.media.thread")
            if not thread_elements:
                print("当前页面没有找到帖子列表。")
                break

            print(f"在第 {current_page} 页找到 {len(thread_elements)} 个帖子，开始过滤...")
            for item in thread_elements:
                # 检查帖子是否属于任何一个被排除的板块
                excluded = False
                for forum_href in EXCLUDED_FORUMS:
                    if item.query_selector(f"a[href='{forum_href}']"):
                        title_element = item.query_selector("div.subject.break-all > a")
                        title = title_element.inner_text() if title_element else "未知标题"
                        print(f"  - [跳过] 发现被排除板块的帖子: {title.strip()}")
                        excluded = True
                        break
                if excluded:
                    continue
                
                link_element = item.query_selector("div.subject.break-all > a")
                if link_element:
                    title = link_element.inner_text().strip()
                    href = link_element.get_attribute("href")
                    full_url = f"{BASE_URL}/{href}"
                    if full_url not in processed_urls:
                        collected_links.append({"title": title, "url": full_url})
                        processed_urls.add(full_url)
                        print(f"  + [收录] {title}")
                        # 如果是快速测试模式，检查是否已达到数量限制
                        if QUICK_TEST_MODE and len(collected_links) >= QUICK_TEST_LIMIT:
                            print(f"\n快速测试模式已启动，并达到 {QUICK_TEST_LIMIT} 个链接的抓取上限，停止采集。")
                            break # 跳出当前页的循环

            # 再次检查是否因为快速模式而需要跳出外层循环
            if QUICK_TEST_MODE and len(collected_links) >= QUICK_TEST_LIMIT:
                break # 跳出翻页循环

            # 寻找并点击“下一页”
            try:
                next_page_button = page.locator("a.page-link:has-text('▶')")
                if next_page_button.count() > 0:
                    print("找到'下一页'按钮，准备翻页...")
                    next_page_button.click()
                    current_page += 1
                    # 等待页面跳转完成
                    page.wait_for_load_state("networkidle", timeout=30000)
                else:
                    print("未找到'下一页'按钮，抓取结束。")
                    break
            except Exception as e:
                print(f"翻页时出错: {e}")
                break
        
        print(f"\n总共收集到 {len(collected_links)} 个有效帖子链接，准备抓取下载地址...")

        # 步骤 4 & 5: 进入帖子抓取媒体链接
        for link_info in collected_links:
            print(f"--- 正在处理: {link_info['title']} ---")
            try:
                page.goto(link_info['url'], timeout=60000, wait_until="domcontentloaded")
                
                # 使用 expect_response 来捕获媒体文件请求
                with page.expect_response(lambda r: r.request.resource_type == "media" or ".mp3" in r.url or ".flac" in r.url, timeout=20000) as response_info:
                    # 尝试点击播放按钮，如果按钮不存在或不可见，可能会超时，但我们依然能通过 expect_response 捕获到链接
                    play_button = page.locator(".aplayer-button, .aplayer-dplayer").first
                    if play_button.is_visible():
                         play_button.click(timeout=5000)
                
                media_response = response_info.value
                media_url = media_response.url
                print(f"  ✅ 抓取成功: {media_url}")
                results.append({"title": link_info['title'], "url": media_url})

            except PlaywrightTimeoutError:
                print(f"  ❌ 处理超时或未找到媒体链接: {link_info['title']}")
            except Exception as e:
                print(f"  ❌ 处理时发生未知错误: {link_info['title']} - {e}")
            
            time.sleep(1) # 每次抓取后稍作停留

        browser.close()

        # 步骤 6: 保存到文件
        with open("music_links.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        print(f"\n🎉 全部完成！成功抓取 {len(results)} 首歌曲，已保存到 music_links.json")

if __name__ == "__main__":
    run()
