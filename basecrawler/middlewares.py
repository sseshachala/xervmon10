from scrapy import log
from scrapy.exceptions import CloseSpider

class ErrorsMiddleware(object):
    def process_spider_exception(self, response, exception, spider):
        exc = str(exception)
        log.msg("PROCESS EXCEPTION: %s" % exc)
        spider.errors.append(exc)
        return []


class ErrorDownloader(object):
    def process_exception(self, request, exception, spider):
        exc = str(exception)
        log.msg("PROCESS DOWNLOADER EXCEPTION: %s" % exc)
        spider.errors.append(exc)
        return None
