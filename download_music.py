import json
import os
import requests
import sys

def download_music():
    # 从命令行参数获取搜索关键词，并用它来命名文件夹
    if len(sys.argv) > 1:
        search_keyword = sys.argv[1]
    else:
        print("请提供一个搜索关键词作为文件夹名称。")
        return

    # 创建与关键词同名的文件夹
    if not os.path.exists(search_keyword):
        os.makedirs(search_keyword)
        print(f"已创建文件夹: {search_keyword}")

    # 读取包含音乐链接的JSON文件
    try:
        with open("music_links.json", "r", encoding="utf-8") as f:
            music_links = json.load(f)
    except FileNotFoundError:
        print("错误: music_links.json 文件未找到。请先运行hifiKeyWordSearch.py。")
        return
    except json.JSONDecodeError:
        print("错误: music_links.json 文件格式不正确。")
        return

    if not music_links:
        print("music_links.json 文件中没有找到任何歌曲链接。")
        return

    print(f"开始从 music_links.json 下载 {len(music_links)} 首歌曲...")

    # 遍历并下载每个链接
    for song in music_links:
        title = song.get("title", "untitled").replace("/", "-") # 防止文件名中包含路径分隔符
        url = song.get("url")

        if not url:
            print(f"  - [跳过] {title} (缺少URL)")
            continue

        # 从URL中猜测文件扩展名
        file_extension = ".flac" if ".flac" in url.lower() else ".mp3"
        file_name = f"{title}{file_extension}"
        file_path = os.path.join(search_keyword, file_name)

        print(f"  - 正在下载: {file_name}")
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()  # 如果请求失败则引发HTTPError

            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"  ✅ 下载成功: {file_name}")

        except requests.exceptions.RequestException as e:
            print(f"  ❌ 下载失败: {title} - {e}")

    print(f"\n🎉 全部下载完成！文件已保存到 '{search_keyword}' 文件夹中。")

if __name__ == "__main__":
    download_music()
