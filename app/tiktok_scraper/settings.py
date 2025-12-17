# =============================================================================
# TikTok爬虫Scrapy项目配置文件
# 
# 该文件包含了TikTok爬虫的所有配置参数，包括性能调优、错误处理、
# Playwright集成、数据管道等关键设置。
# =============================================================================

# 项目名称，用于识别和标识此Scrapy项目
BOT_NAME = "tiktok_scraper"

# Spider模块路径，指定spiders文件夹的位置
# Scrapy会自动在此路径下查找爬虫文件
SPIDER_MODULES = ["tiktok_scraper.spiders"]

# 新爬虫模块路径，用于scrapy genspider命令创建新爬虫的默认路径
NEWSPIDER_MODULE = "tiktok_scraper.spiders"

# =============================================================================
# 基础爬虫设置
# =============================================================================

# 是否遵守robots.txt协议
# False：不遵守，可以抓取所有允许的页面
# True：遵守robots.txt规则，限制较多
ROBOTSTXT_OBEY = False

# =============================================================================
# 并发控制设置
# 控制爬虫的请求并发数，优化性能和避免被反爬
# =============================================================================

# 全局最大并发请求数
# 控制同时进行的请求总数，过高可能被网站限制
CONCURRENT_REQUESTS = 8

# 每个域名最大并发请求数
# 限制对同一域名的并发请求，避免对目标网站造成过大压力
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# 请求间延迟时间（秒）
# 0表示无延迟，根据需要可设置为1-3秒减少反爬风险
DOWNLOAD_DELAY = 0

# 是否随机化下载延迟
# True：延迟时间在0.5*DOWLOAD_DELAY到1.5*DOWNLOAD_DELAY之间随机
# False：固定延迟时间
RANDOMIZE_DOWNLOAD_DELAY = False

# =============================================================================
# 超时和重试设置
# =============================================================================

# 下载超时时间（秒）
# 超过此时间未收到响应则判定为超时
DOWNLOAD_TIMEOUT = 30

# 是否启用重试机制
# True：启用，失败请求会自动重试
RETRY_ENABLED = True

# 最大重试次数
# 每次请求失败后的重试次数
RETRY_TIMES = 2

# 需要重试的HTTP状态码列表
# 遇到这些状态码时会触发重试机制
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
# 500：服务器内部错误
# 502：网关错误
# 503：服务不可用
# 504：网关超时
# 408：请求超时
# 429：请求过多（速率限制）

# =============================================================================
# 下载中间件配置
# 中间件用于处理请求和响应的预处理/后处理
# =============================================================================

DOWNLOADER_MIDDLEWARES = {
    # 禁用默认的User-Agent中间件
    # 手动设置User-Agent时需要禁用默认的，避免冲突
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    
    # 重试中间件，优先级90
    # 负责处理请求失败后的自动重试逻辑
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
    
    # HTTP压缩中间件，优先级810
    # 处理gzip、deflate等压缩格式的响应，提高传输效率
    "scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware": 810,
}

# =============================================================================
# 下载处理器配置
# 指定不同协议的下载处理方式
# =============================================================================

DOWNLOAD_HANDLERS = {
    # HTTP协议使用Playwright下载处理器
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    
    # HTTPS协议使用Playwright下载处理器
    # 确保HTTPS请求也使用Playwright处理JavaScript渲染
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# =============================================================================
# Twisted事件循环 reactor 配置
# 用于集成asyncio和Twisted，处理异步操作
# =============================================================================

# 使用asyncio兼容的reactor，支持现代异步编程模式
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# =============================================================================
# Playwright浏览器配置
# 配置浏览器启动参数，优化性能和反检测
# =============================================================================

# 浏览器类型：chromium、firefox、webkit
PLAYWRIGHT_BROWSER_TYPE = "chromium"

# 浏览器启动选项
PLAYWRIGHT_LAUNCH_OPTIONS = {
    # 无头模式，不显示浏览器窗口，提高性能
    "headless": True,
    
    # 浏览器启动参数列表
    "args": [
        # 禁用自动化控制检测特征
        "--disable-blink-features=AutomationControlled",
        
        # 禁用/dev/shm使用，避免容器环境下的内存问题
        "--disable-dev-shm-usage",
        
        # 禁用沙盒模式，在某些环境下需要
        "--no-sandbox",
        
        # 禁用GPU硬件加速
        "--disable-gpu",
        
        # 禁用软件光栅化器
        "--disable-software-rasterizer",
        
        # 禁用扩展程序
        "--disable-extensions",
        
        # 禁用插件
        "--disable-plugins",
        
        # 禁用后台网络请求
        "--disable-background-networking",
        
        # 禁用默认应用
        "--disable-default-apps",
        
        # 禁用同步功能
        "--disable-sync",
        
        # 禁用翻译功能
        "--disable-translate",
        
        # 隐藏滚动条
        "--hide-scrollbars",
        
        # 只记录指标数据
        "--metrics-recording-only",
        
        # 静音音频
        "--mute-audio",
        
        # 跳过首次运行设置
        "--no-first-run",
        
        # 禁用安全浏览自动更新
        "--safebrowsing-disable-auto-update",
        
        # 忽略证书错误
        "--ignore-certificate-errors",
        "--ignore-ssl-errors",
        "--ignore-certificate-errors-spki-list",
    ]
}

# =============================================================================
# Playwright性能优化设置
# 控制浏览器上下文和页面的最大数量
# =============================================================================

# 最大浏览器上下文数量
# 上下文是浏览器中的隔离环境，类似无痕模式
PLAYWRIGHT_MAX_CONTEXTS = 8

# 每个上下文的最大页面数
# 控制每个浏览器上下文中的标签页数量
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 1

# 默认页面导航超时时间（毫秒）
# 页面加载和导航操作的超时限制
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 15000

# =============================================================================
# 数据管道配置
# 定义数据处理管道的执行顺序
# =============================================================================

ITEM_PIPELINES = {
    # JSON管道，优先级300
    # 将抓取的数据保存为JSON格式文件
    "tiktok_scraper.pipelines.JsonPipeline": 300,
}

# =============================================================================
# 日志和错误处理设置
# =============================================================================

# 日志级别
# ERROR：只记录错误信息，减少日志输出
LOG_LEVEL = "ERROR"

# 错误计数爬虫关闭条件
# 0表示不根据错误数量自动关闭爬虫
CLOSESPIDER_ERRORCOUNT = 0

# =============================================================================
# 配置说明
# 
# 此配置文件针对TikTok网站的特殊性质进行了优化：
# 1. 使用Playwright处理JavaScript渲染
# 2. 优化并发数避免触发反爬机制
# 3. 配置适当的重试和超时策略
# 4. 禁用不必要的功能提高性能
# 5. 添加反检测参数模拟真实浏览器
# 
# 使用建议：
# - 根据目标网站的反爬强度调整CONCURRENT_REQUESTS和DOWNLOAD_DELAY
# - 监控错误日志，适当调整RETRY相关参数
# - 在生产环境中可能需要增加USER_AGENT轮换和代理支持
# =============================================================================