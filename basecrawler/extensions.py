from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher

class FailLogger(object):
    def __init__(self):
        dispatcher.connect(self.spider_error, signal=signals.spider_error)

    def spider_error(self, failure, response, spider):
        spider.errors.append(failure.getTraceback())
                
