# HiFiNi 音乐助手 - 安卓版开发计划

## 1. 项目概述

本项目的目标是将 `hifiKeyWordSearch.py` 脚本的功能，转化为一个成熟、可用的安卓手机应用。用户将能通过该 App 搜索、发现并在线播放来自 HiFiNi 网站的音乐资源。

由于移动端环境的限制（无法直接运行 Playwright 和桌面浏览器），我们不能将 Python 脚本直接嵌入 App。因此，本项目将采用标准的**客户端-服务器 (Client-Server)**架构来实现。

---

## 2. 核心架构

我们将项目拆分为两个独立但紧密协作的部分：

- **后端服务 (Backend Service)**: 一个基于 Python 的网络 API，负责执行所有的数据抓取和处理工作。
- **安卓客户端 (Android Client)**: 用户手机上安装的原生 App，负责提供交互界面、发送请求和播放音乐。

**数据流程如下:**

```
[安卓 App] ---> [互联网 API 请求] ---> [Python 后端服务器] ---> [运行 Playwright 抓取 hifiti.com] ---> [返回 JSON 数据] ---> [安卓 App] ---> [解析并展示/播放]
```

---

## 3. 后端服务开发 (Backend)

后端是整个项目的大脑，它将我们的抓取脚本封装成一个可供任何客户端（不止是我们的安卓 App）调用的网络服务。

- **技术栈:**
  - **Python 3**: 核心语言。
  - **FastAPI**: 一个现代、高性能的 Python Web 框架，用于快速创建 API。
  - **Playwright**: 执行网页自动化和数据抓取的核心库。
  - **Uvicorn**: 一个 ASGI 服务器，用于运行我们的 FastAPI 应用。

- **核心任务:**
  1. **脚本 API 化**: 将 `hifiKeyWordSearch.py` 的核心逻辑重构为一个函数，例如 `search_music(keyword: str)`。
  2. **创建 API 端点**: 使用 FastAPI 创建一个网络接口，例如 `/api/search`。
  3. **处理请求**: 该接口接收一个 `keyword` 参数，调用 `search_music` 函数。
  4. **返回 JSON**: 函数执行完毕后，将抓取到的歌曲列表（包含标题和播放 URL）以 JSON 格式作为 HTTP 响应返回给客户端。
  5. **配置化**: 将抓取逻辑中的可变参数（如 `MAX_PAGES`, `QUICK_TEST_MODE`, `EXCLUDED_FORUMS`）改造为 API 的查询参数，增加灵活性。

- **部署:**
  为了让全球的 App 用户都能访问，这个 Python 服务需要被部署在一台拥有公网 IP 的服务器上（例如：阿里云、腾讯云、Vultr、Heroku 等）。

---

## 4. 安卓客户端开发 (Android)

安卓客户端是用户直接交互的界面，它的核心是提供优秀的用户体验。

- **技术栈:**
  - **Kotlin**: Google 官方推荐的安卓开发语言。
  - **Jetpack Compose**: 用于构建原生 UI 的现代化声明式框架。
  - **Retrofit**: 一个强大的类型安全的 HTTP 客户端，用于与我们的后端 API 进行通信。
  - **ExoPlayer**: 一个由 Google 开发的、功能强大且可扩展的开源媒体播放库，用于播放在线音乐。

- **核心任务:**
  1. **UI 设计**:
     - 一个包含搜索框和搜索按钮的主界面。
     - 一个用于展示搜索结果的列表（使用 `LazyColumn`)。
     - 一个简洁的底部播放控制条。
  2. **网络请求**:
     - 使用 Retrofit 定义一个服务接口，用于调用后端部署好的 `/api/search` API。
  3. **数据处理**:
     - 创建一个数据类（`data class Song`）来匹配从后端接收的 JSON 结构。
     - 使用序列化库（如 `kotlinx.serialization` 或 `Gson`）将 JSON 自动转换为 `Song` 对象列表。
  4. **音乐播放**:
     - 集成 ExoPlayer。
     - 当用户点击结果列表中的某一项时，获取其 `url`，并交由 ExoPlayer 进行在线流式播放。

---

## 5. 开发路线图 (Roadmap)

1.  **第一步：后端 API 化**:
    - 安装 `fastapi` 和 `uvicorn`。
    - 创建 `main.py`，将现有脚本逻辑封装成一个可以通过 HTTP 访问的 API。
    - 在本地成功运行并测试该 API。

2.  **第二步：安卓 App 基础搭建**:
    - 使用 Android Studio 创建一个新的 Jetpack Compose 项目。
    - 完成搜索界面和结果列表的基本 UI 布局。

3.  **第三步：前后端联调**:
    - 在 App 中集成 Retrofit，并配置其指向本地运行的后端服务地址。
    - 实现 App 的搜索功能，确保可以成功获取数据并在列表中展示。

4.  **第四步：播放功能实现**:
    - 在 App 中集成 ExoPlayer。
    - 实现点击列表项后，自动播放对应音乐的功能。

5.  **第五步：部署与发布**:
    - 将 Python 后端应用部署到云服务器。
    - 将 App 中的 API 地址更新为服务器的公网地址。
    - 对 App 进行打包、签名，准备发布。
