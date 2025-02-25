from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
# from plugins import PluginSpider

def run_spider():
    process = CrawlerProcess(get_project_settings())
    process.crawl(PluginSpider)
    process.start()

if __name__ == '__main__':
    run_spider()