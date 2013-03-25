# Scrapy settings for comcast project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
from basecrawler.base_settings import *

BOT_NAME = 'hpcloud2'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['hpcloud2.spiders']
NEWSPIDER_MODULE = 'hpcloud2.spiders'


# server reports period set on server side
# so we need to wait and make in sequentially
DOWNLOAD_DELAY = 0.25
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1



ITEM_PIPELINES = [
         'hpcloud2.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]


URLS = dict(
        _LOGIN_URL = (
            'https://console.hpcloud.com/login'
            #'https://console.hpcloud.com/invoices?year=2012'
            ),
        _BILLS_URL = (
            #'https://console.hpcloud.com/invoices'
            'https://console.hpcloud.com/invoices?year=2012'
          ),
        )

