from scrapy import log

class ErrorsMiddleware(object):
    def process_spider_exception(self, response, exception, spider):
        log.msg("PROCESS EXCEPTION")
        spider.errors.append(str(exception))
        return []
