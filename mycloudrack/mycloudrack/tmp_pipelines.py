#!/usr/bin/env python

from scrapy.conf import settings
from scrapy import log
from urlparse import urljoin




class UrlPipeline(object):
    def __init__(self):
        self.base_url = None

    def open_spider(self, spider):
        urls = settings.get('URLS')
        base_url = settings.get('BASE_URL')
        specific_urls = settings.get("SPECIFIC_URLS")
        if not self.base_url:
            self.base_url = base_url

        specific_url = specific_urls.get(self.base_url, {})
        for attr, url in urls.items():
            if attr in specific_url:
                url = specific_url[attr]
            setattr(spider, attr, urljoin(self.base_url, url))
