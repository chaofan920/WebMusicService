// 引入我们需要的两个小伙伴：Express 和 Playwright
const express = require('express');
const { chromium } = require('playwright');

// --- 配置区 ---
// 你的 HiFiNi 账号信息，要好好保管哦~
const USERNAME = "zhuzhuzhuzhu";
const PASSWORD = "CHAOfan0920";

// --- HTML / CSS / JavaScript 前端代码 ---
// 这部分和之前一模一样，我们只是把它从 Python 的世界搬到了 JavaScript 的怀抱里
const HTML_CONTENT = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HiFiNi 音乐抓取器 (JS版)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .loader {
            border: 5px solid #f3f3f3;
            border-top: 5px solid #5865f2;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body class="bg-gray-100 text-gray-800 font-sans">
    <div class="container mx-auto p-4 sm:p-6 md:p-8 max-w-2xl">
        <div class="bg-white p-6 rounded-xl shadow-lg">
            <h1 class="text-2xl sm:text-3xl font-bold text-center mb-2 text-indigo-600">HiFiNi 音乐小助手 🎵 (JS Ver.)</h1>
            <p class="text-center text-gray-500 mb-6">输入想听的歌手或歌名，剩下的交给我吧~</p>
            
            <div class="flex flex-col sm:flex-row gap-2">
                <input type="text" id="keyword" placeholder="例如: 周杰伦" class="flex-grow w-full px-4 py-2 text-lg border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 outline-none transition">
                <button id="search-btn" class="w-full sm:w-auto bg-indigo-500 hover:bg-indigo-600 text-white font-bold py-2 px-6 rounded-lg text-lg transition-transform transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:ring-opacity-75">
                    <span>开始搜索</span>
                </button>
            </div>
        </div>

        <div id="status-container" class="mt-6 text-center">
            <div id="loader" class="loader mx-auto hidden"></div>
            <p id="status-text" class="text-gray-600 mt-4 text-lg"></p>
        </div>

        <div id="results-container" class="mt-6">
             <ul id="results-list" class="space-y-3">
                <!-- 搜索结果会在这里显示 -->
             </ul>
        </div>
    </div>

    <script>
        const searchBtn = document.getElementById('search-btn');
        const keywordInput = document.getElementById('keyword');
        const loader = document.getElementById('loader');
        const statusText = document.getElementById('status-text');
        const resultsList = document.getElementById('results-list');

        keywordInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                searchBtn.click();
            }
        });

        searchBtn.addEventListener('click', async () => {
            const keyword = keywordInput.value.trim();
            if (!keyword) {
                statusText.textContent = '哎呀，关键词不能为空哦~';
                return;
            }

            loader.classList.remove('hidden');
            statusText.textContent = '收到指令！正在启动浏览器登录，请稍等片刻...';
            resultsList.innerHTML = '';
            searchBtn.disabled = true;
            searchBtn.classList.add('opacity-50', 'cursor-not-allowed');
            searchBtn.querySelector('span').textContent = '搜索中...';

            try {
                const response = await fetch(\`/api/search?keyword=\${encodeURIComponent(keyword)}\`);
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || '服务器好像开小差了...');
                }

                const data = await response.json();
                
                loader.classList.add('hidden');
                if (data.length === 0) {
                    statusText.textContent = '好可惜，没有找到相关的歌曲呢... 换个词试试？';
                } else {
                    statusText.textContent = \`太棒了！为你找到了 \${data.length} 首歌曲~\`;
                    data.forEach(song => {
                        const li = document.createElement('li');
                        li.className = 'bg-white p-4 rounded-lg shadow-md flex items-center justify-between transition-transform transform hover:scale-102';
                        
                        const titleSpan = document.createElement('span');
                        titleSpan.textContent = song.title;
                        titleSpan.className = 'flex-grow mr-4 text-gray-700';

                        const downloadLink = document.createElement('a');
                        downloadLink.href = song.url;
                        downloadLink.textContent = '下载';
                        downloadLink.setAttribute('download', song.title.replace(/ /g, '_') + '.mp3');
                        downloadLink.className = 'bg-green-500 hover:bg-green-600 text-white font-bold py-1 px-4 rounded-full text-sm transition';
                        
                        li.appendChild(titleSpan);
                        li.appendChild(downloadLink);
                        resultsList.appendChild(li);
                    });
                }

            } catch (error) {
                loader.classList.add('hidden');
                statusText.textContent = \`出错了: \${error.message}\`;
            } finally {
                searchBtn.disabled = false;
                searchBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                searchBtn.querySelector('span').textContent = '开始搜索';
            }
        });
    </script>
</body>
</html>
`;

// --- Express 后端应用 ---
const app = express();
const PORT = 8000;
let browserContext = null;

async function scrapeHifini(page, keyword) {
    const allMusicData = [];
    
    // 步骤 1: 登录 (如果需要)
    try {
        // 增加超时时间到30秒，并等待DOM加载完成即可
        await page.goto("https://hifiti.com/", { timeout: 30000, waitUntil: 'domcontentloaded' });
        const loginButton = page.locator('a[href*="user-login.htm"]');
        if (await loginButton.count() > 0) {
            console.log("尚未登录，现在开始执行登录流程...");
            await page.goto("https://hifiti.com/user-login.htm", { timeout: 20000, waitUntil: 'domcontentloaded' });
            await page.getByPlaceholder("请输入用户名").fill(USERNAME);
            await page.getByPlaceholder("请输入密码").fill(PASSWORD);
            await page.getByRole("button", { name: "登录" }).click();
            await page.waitForURL("https://hifiti.com/", { timeout: 20000 });
            console.log("登录成功！🎉");
        } else {
            console.log("检测到已登录，跳过登录步骤。");
        }
    } catch (e) {
        console.error(`登录或检查登录状态时出错: ${e}`);
        throw new Error(`登录失败: ${e.message}`);
    }

    // 步骤 2: 搜索关键词
    console.log(`开始搜索关键词 '${keyword}'...`);
    try {
        await page.locator("#searchKeyword").fill(keyword);
        await page.locator(".btn.btn-primary").click();
        await page.waitForLoadState("domcontentloaded");
    } catch (e) {
        console.error(`搜索失败: ${e}`);
        throw new Error(`搜索失败: ${e.message}`);
    }

    // 步骤 3: 采集帖子链接
    const songLinksLocators = page.locator('a.subject.break-all');
    const count = await songLinksLocators.count();
    if (count === 0) return [];
    
    const songsToProcess = [];
    const maxSongs = Math.min(count, 10); // 同样只处理前10个，避免等待太久
    console.log(`找到了 ${count} 个帖子，将处理前 ${maxSongs} 个...`);
    for (let i = 0; i < maxSongs; i++) {
        const locator = songLinksLocators.nth(i);
        const title = await locator.innerText();
        const href = await locator.getAttribute("href");
        if (href) {
            const fullUrl = `https://hifiti.com/${href}`;
            songsToProcess.push({ title: title.trim(), post_url: fullUrl });
        }
    }

    // 步骤 4 & 5: 进入帖子抓取媒体链接
    for (const [index, songInfo] of songsToProcess.entries()) {
        console.log(`--- 处理第 ${index + 1}/${songsToProcess.length} 首：${songInfo.title} ---`);
        let requestListener = null;
        try {
            const mediaUrlPromise = new Promise((resolve, reject) => {
                requestListener = (request) => {
                    const url = request.url();
                    if (url.match(/\.(mp3|flac)(\?.*)?$/)) {
                        console.log(`🎶 抓取成功 -> ${url}`);
                        resolve(url);
                    }
                };
                page.on('request', requestListener);
                // 设置一个20秒的超时定时器
                setTimeout(() => reject(new Error('超时未抓取到媒体链接')), 20000);
            });

            await page.goto(songInfo.post_url, { waitUntil: "domcontentloaded", timeout: 20000 });
            const playButton = page.locator("div.aplayer-button.aplayer-play");
            await playButton.waitFor({ timeout: 15000 });
            await playButton.click();

            const finalUrl = await mediaUrlPromise;
            allMusicData.push({ title: songInfo.title, url: finalUrl });

        } catch (e) {
            console.error(`❌ 处理帖子 ${songInfo.post_url} 时出错: ${e.message}`);
        } finally {
            // 处理完一个页面，一定要把监听器移除，避免干扰下一个
            if (requestListener) {
                page.removeListener('request', requestListener);
            }
        }
    }
    return allMusicData;
}

// API 路由，负责处理搜索请求
app.get('/api/search', async (req, res) => {
    const keyword = req.query.keyword;
    if (!browserContext) {
        return res.status(503).json({ detail: "浏览器服务尚未准备好，请稍后再试。" });
    }
    if (!keyword) {
        return res.status(400).json({ detail: "关键词不能为空哦！" });
    }
    
    const page = await browserContext.newPage();
    try {
        const results = await scrapeHifini(page, keyword);
        res.json(results);
    } catch (error) {
        res.status(500).json({ detail: error.message || '发生了未知错误' });
    } finally {
        await page.close(); // 每次请求完成后关闭页面，保持环境干净
    }
});

// 根路由，提供我们的HTML页面
app.get('/', (req, res) => {
    res.send(HTML_CONTENT);
});

// --- 启动器 ---
// 使用一个立即执行的异步函数来初始化浏览器并启动服务器
(async () => {
    console.log("应用启动中，正在初始化Playwright...");
    const browser = await chromium.launch({ headless: true }); // headless: true 表示在后台运行
    browserContext = await browser.newContext();
    console.log("Playwright初始化完成！");

    app.listen(PORT, () => {
        console.log("="*50);
        console.log(`🎵 HiFiNi 音乐小助手 (JS版) 已启动！`);
        console.log(`请在浏览器中打开 http://127.0.0.1:${PORT} 访问我哦~`);
        console.log("="*50);
    });
})();
