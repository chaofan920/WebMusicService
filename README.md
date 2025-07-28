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

## 4. 安卓客户端开发详解 (Android Client Blueprint)

安卓客户端是用户直接交互的界面。以下是构建该 App 的核心思路与关键代码，使用 Google 推荐的现代化技术栈。

- **技术栈总览:**
  - **语言**: Kotlin
  - **UI 框架**: Jetpack Compose
  - **网络请求**: Retrofit
  - **JSON 解析**: Kotlinx Serialization
  - **音乐播放**: ExoPlayer
  - **架构**: MVVM (Model-View-ViewModel)

### 第 1 步：项目设置 (build.gradle.kts)

在 App 模块的 `build.gradle.kts` 文件中添加所有必要的库依赖：

```kotlin
// 在 build.gradle.kts 的 dependencies { ... } 代码块中添加

// Retrofit for networking
implementation("com.squareup.retrofit2:retrofit:2.9.0")

// Kotlinx Serialization for JSON parsing
implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.0")
implementation("com.jakewharton.retrofit:retrofit2-kotlinx-serialization-converter:1.0.0")

// ExoPlayer for media playback
implementation("androidx.media3:media3-exoplayer:1.2.0")

// Jetpack Compose dependencies (usually already there)
implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.6.2")
```

### 第 2 步：定义数据模型 (Song.kt)

创建一个数据类来匹配 API 返回的 JSON 结构。

```kotlin
import kotlinx.serialization.Serializable

@Serializable
data class Song(
    val title: String,
    val url: String
)
```

### 第 3 步：创建网络服务接口 (ApiService.kt)

使用 Retrofit 定义一个接口，来描述如何与我们的后端 API 通信。

```kotlin
import retrofit2.http.GET
import retrofit2.http.Query

interface ApiService {

    @GET("/api/search") // 对应 FastAPI 中的端点
    suspend fun searchMusic(
        @Query("keyword") keyword: String,
        @Query("quick") quick: Boolean = false,
        @Query("limit") limit: Int = 10,
        @Query("pages") pages: Int = 3,
        @Query("exclude") exclude: String = "forum-7.htm"
    ): List<Song> // Retrofit 会自动将返回的 JSON 解析成 Song 列表
}
```

### 第 4 步：创建 ViewModel 管理业务逻辑 (SearchViewModel.kt)

ViewModel 是连接 UI 和数据（我们的 API）的桥梁。

```kotlin
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType

class SearchViewModel : ViewModel() {

    // 注意：在安卓模拟器中，要用 10.0.2.2 访问你电脑的 localhost
    private val BASE_URL = "http://10.0.2.2:8000"

    private val apiService: ApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(Json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(ApiService::class.java)
    }

    private val _songs = MutableStateFlow<List<Song>>(emptyList())
    val songs = _songs.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading = _isLoading.asStateFlow()

    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage = _errorMessage.asStateFlow()

    fun search(keyword: String) {
        if (keyword.isBlank()) return
        viewModelScope.launch {
            _isLoading.value = true
            _errorMessage.value = null
            try {
                val results = apiService.searchMusic(keyword = keyword)
                _songs.value = results
            } catch (e: Exception) {
                _errorMessage.value = "搜索失败: ${e.message}"
                _songs.value = emptyList()
            } finally {
                _isLoading.value = false
            }
        }
    }
}
```

### 第 5 步：构建 UI 界面 (SearchScreen.kt)

使用 Jetpack Compose 来构建用户界面。

```kotlin
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
fun SearchScreen(searchViewModel: SearchViewModel = viewModel()) {
    val songs by searchViewModel.songs.collectAsState()
    val isLoading by searchViewModel.isLoading.collectAsState()
    val errorMessage by searchViewModel.errorMessage.collectAsState()
    var text by remember { mutableStateOf("") }

    Column(modifier = Modifier.padding(16.dp)) {
        // ... (搜索栏和按钮的代码)

        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            if (isLoading) {
                CircularProgressIndicator()
            } else if (errorMessage != null) {
                Text(text = errorMessage!!)
            } else {
                LazyColumn {
                    items(songs) { song ->
                        SongItem(song = song, onPlayClick = { /* TODO */ })
                        Divider()
                    }
                }
            }
        }
    }
}

@Composable
fun SongItem(song: Song, onPlayClick: (Song) -> Unit) {
    // ... (列表项 UI 的代码)
}
```

### 第 6 步：集成播放器

通过一个单例 `PlayerManager` 来管理 ExoPlayer 实例，并在 ViewModel 中调用它。

```kotlin
// PlayerManager.kt
object PlayerManager {
    private var exoPlayer: ExoPlayer? = null
    fun getPlayer(context: Context): ExoPlayer {
        if (exoPlayer == null) {
            exoPlayer = ExoPlayer.Builder(context).build()
        }
        return exoPlayer!!
    }
    // ... (省略释放逻辑)
}

// 在 SearchViewModel.kt 中添加
fun playSong(context: Context, song: Song) {
    val player = PlayerManager.getPlayer(context)
    val mediaItem = androidx.media3.common.MediaItem.fromUri(song.url)
    player.setMediaItem(mediaItem)
    player.prepare()
    player.play()
}
```

### 第 7 步：添加网络权限 (AndroidManifest.xml)

在 `app/src/main/AndroidManifest.xml` 文件中声明应用需要网络权限。

```xml
<manifest ...>
    <uses-permission android:name="android.permission.INTERNET" />
    <application ...> ... </application>
</manifest>
```

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
    - 在 App 中集成 Retrofit，并配置其指向本地运行的后端服务地址 (`http://10.0.2.2:8000`)。
    - 实现 App 的搜索功能，确保可以成功获取数据并在列表中展示。

4.  **第四步：播放功能实现**:
    - 在 App 中集成 ExoPlayer。
    - 实现点击列表项后，自动播放对应音乐的功能。

5.  **第五步：部署与发布**:
    - 将 Python 后端应用部署到云服务器。
    - 将 App 中的 API 地址更新为服务器的公网地址。
    - 对 App 进行打包、签名，准备发布。