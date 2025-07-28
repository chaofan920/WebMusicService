#!/bin/bash

# 脚本：自动搜索并下载HIFI音乐
# 用法: ./run_music_downloader.sh "您要搜索的关键词"

# --- 配置 ---
# 获取脚本所在的绝对路径
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
# Python虚拟环境的解释器路径
PYTHON_EXEC="${SCRIPT_DIR}/venv/bin/python"
# 搜索脚本的路径
SEARCH_SCRIPT="${SCRIPT_DIR}/hifiKeyWordSearch.py"
# 下载脚本的路径
DOWNLOAD_SCRIPT="${SCRIPT_DIR}/download_music.py"


# --- 主逻辑 ---

# 检查是否提供了搜索关键词
if [ -n "$1" ]; then
  KEYWORD="$1"
else
  # 如果没有提供参数，则提示用户输入
  read -p "请输入您要搜索的关键词: " KEYWORD
fi

# 如果用户没有输入任何内容，则退出
if [ -z "$KEYWORD" ]; then
    echo "错误：没有提供搜索关键词。"
    exit 1
fi

echo "=================================================="
echo " STEP 1: 开始搜索关键词 - '$KEYWORD'"
echo "=================================================="
"$PYTHON_EXEC" "$SEARCH_SCRIPT" "$KEYWORD"

# 检查上一步是否成功
if [ $? -ne 0 ]; then
  echo "错误：搜索脚本执行失败。正在中止操作。"
  exit 1
fi

echo ""
echo "=================================================="
echo " STEP 2: 开始下载歌曲到文件夹 - '$KEYWORD'"
echo "=================================================="
"$PYTHON_EXEC" "$DOWNLOAD_SCRIPT" "$KEYWORD"

if [ $? -ne 0 ]; then
  echo "错误：下载脚本执行失败。"
  exit 1
fi

echo ""
echo "=================================================="
echo " ✅ 全部完成！"
echo "=================================================="
