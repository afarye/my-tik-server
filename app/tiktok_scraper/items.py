import scrapy

class TikTokItem(scrapy.Item):
    url = scrapy.Field()
    username = scrapy.Field()
    following = scrapy.Field()
    followers = scrapy.Field()
    likes = scrapy.Field()
    video_count = scrapy.Field()


