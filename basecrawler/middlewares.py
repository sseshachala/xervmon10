from scrapy import log
from scrapy.exceptions import CloseSpider
from scrapy.contrib.middleware.spidermiddleware.httperror import HttpError

class ErrorsMiddleware(object):
    def process_spider_exception(self, response, exception, spider):
        if isinstance(exception, HttpError):
            return []
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
