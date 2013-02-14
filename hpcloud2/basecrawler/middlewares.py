from scrapy import log
from scrapy.exceptions import CloseSpider

class ErrorsMiddleware(object):
    def process_spider_exception(self, response, exception, spider):
        log.msg("PROCESS EXCEPTION")
        spider.errors.append(str(exception))
        raise CloseSpider(str(exception))
        return []
        
class ErrorDownloader(object):
    def process_exception(self, request, exception, spider):
        log.msg("PROCESS DOWNLOADER EXCEPTION")
        spider.errors.append(str(exception))
        return None
