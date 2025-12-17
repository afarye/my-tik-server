import scrapy
import json
from tiktok_scraper.items import TikTokItem
from scrapy_playwright.page import PageMethod

class TikTokSpider(scrapy.Spider):
    """
    TikTok用户信息爬虫
    
    该爬虫专门用于从TikTok网站抓取用户的基本信息，包括：
    - 用户名 (username)
    - 关注数 (following)
    - 粉丝数 (followers) 
    - 获赞数 (likes)
    - 视频数 (video_count)
    
    使用Playwright处理JavaScript渲染的页面，确保能够正确获取TikTok的动态内容。
    """
    name = "tiktok"  # 爬虫名称，用于启动爬虫时调用
    
    # 自定义设置：阻止加载静态资源以提高性能
    custom_settings = {
        'PLAYWRIGHT_ABORT_REQUEST': lambda req: req.resource_type in ["image", "media", "font", "stylesheet", "other"]
        # 阻止加载图片、媒体文件、字体、样式表等静态资源，只保留HTML和JS内容
    }

    def __init__(self, urls=None, *args, **kwargs):
        """
        初始化爬虫实例
        
        Args:
            urls (str|list): TikTok用户页面的URL列表
                           - 如果是字符串，用逗号分隔多个URL
                           - 如果是列表，直接使用列表中的URL
                           - 如果是None，使用空列表
        
        Args:
            *args: 父类参数
            **kwargs: 父类关键字参数
        """
        super().__init__(*args, **kwargs)  # 调用父类初始化方法
        
        # 处理起始URL列表
        if isinstance(urls, str):
            # 如果urls是字符串，按逗号分割并清理空白字符
            self.start_urls = [u.strip() for u in urls.split(",") if u.strip()]
        elif isinstance(urls, list):
            # 如果urls已经是列表，直接使用
            self.start_urls = urls
        else:
            # 其他情况（通常为None），使用空列表
            self.start_urls = urls or []

    def start_requests(self):
        """
        生成初始请求
        
        这是Scrapy的入口方法，为每个起始URL生成一个Request对象。
        使用Playwright处理JavaScript渲染，确保能够获取完整的页面内容。
        
        Yields:
            scrapy.Request: 配置好的请求对象，包含所有必要的元数据
        """
        for url in self.start_urls:
            # 使用移动端User-Agent，TikTok对移动端支持更好
            mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
            
            # 创建Request对象
            yield scrapy.Request(
                url=url,  # 目标URL
                callback=self.parse_user,  # 成功响应后的回调函数
                errback=self.errback_close_page,  # 请求失败时的错误处理函数
                headers={"User-Agent": mobile_ua},  # 请求头设置
                meta={
                    # 启用Playwright处理
                    "playwright": True,
                    "playwright_include_page": True,  # 在meta中包含page对象
                    
                    # 页面加载完成后的执行方法
                    "playwright_page_methods": [
                        PageMethod(
                            "wait_for_selector", 
                            "script#__UNIVERSAL_DATA_FOR_REHYDRATION__",  # 等待TikTok的通用数据脚本加载
                            state="attached",  # 元素挂载就绪
                            timeout=5000  # 5秒超时
                        ),
                    ],
                    
                    # 页面导航参数
                    "playwright_page_goto_kwargs": {
                        "wait_until": "domcontentloaded",  # 等待DOM内容加载完成
                        "timeout": 15000,  # 15秒超时
                    },
                },
                dont_filter=True,  # 不过滤重复URL，允许重复请求同一URL
            )

    async def parse_user(self, response):
        """
        解析用户信息
        
        从TikTok页面中提取用户的基本统计数据。
        通过解析页面中的JavaScript数据来获取信息。
        
        Args:
            response (scrapy.Response): 响应对象，包含页面内容和Playwright page对象
            
        Returns:
            TikTokItem: 包含用户信息的数据项
        """
        item = TikTokItem()  # 创建数据项实例
        item["url"] = response.url  # 保存原始URL
        
        # 初始化数据字段
        username = ""
        following = ""
        followers = ""
        likes = ""
        video_count = ""

        # 获取Playwright page对象
        page = response.meta.get("playwright_page")
        
        try:
            # 提取TikTok的通用数据脚本内容
            script_text = response.css("script#__UNIVERSAL_DATA_FOR_REHYDRATION__::text").get()
            
            if script_text:
                try:
                    # 解析JSON数据
                    data = json.loads(script_text)
                    
                    # 提取用户信息
                    user_detail = data.get("__DEFAULT_SCOPE__", {}).get("webapp.user-detail", {})
                    if user_detail:
                        user_info = user_detail.get("userInfo", {}) or {}
                        
                        # 提取用户名
                        username = user_info.get("uniqueId") or (user_info.get("user") or {}).get("uniqueId") or ""
                        
                        # 提取统计数据
                        stats = user_info.get("stats", {}) or {}
                        following = str(stats.get("followingCount", "")) or ""
                        followers = str(stats.get("followerCount", "")) or ""
                        likes = str(stats.get("heartCount", "")) or ""
                        video_count = str(stats.get("videoCount", "")) or ""
                        
                except Exception as e:
                    # JSON解析错误日志
                    self.logger.error(f"JSON parse error for {response.url}: {e}")
                    
        except Exception as e:
            # 页面解析错误日志
            self.logger.error(f"Error parsing {response.url}: {e}")
            
        finally:
            # 确保Playwright页面被正确关闭，释放资源
            if page:
                try:
                    await page.close()
                except:
                    pass  # 忽略关闭时的任何异常

        # 填充数据项
        item["username"] = username
        item["following"] = following
        item["followers"] = followers
        item["likes"] = likes
        item["video_count"] = video_count
        
        # 返回数据项
        yield item

    async def errback_close_page(self, failure):
        """
        错误处理回调函数
        
        当请求失败时关闭Playwright页面并返回空的数据项，
        确保资源被正确释放。
        
        Args:
            failure (twisted.python.failure.Failure): 失败对象，包含错误信息
        """
        # 尝试关闭Playwright页面
        page = failure.request.meta.get("playwright_page")
        if page:
            try:
                await page.close()
            except:
                pass  # 忽略关闭时的任何异常
        
        # 创建空的数据项记录失败情况
        item = TikTokItem()
        item["url"] = failure.request.url
        item["username"] = ""
        item["following"] = ""
        item["followers"] = ""
        item["likes"] = ""
        item["video_count"] = ""
        yield item