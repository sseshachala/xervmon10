# Scrapy settings for comcast project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
from basecrawler.base_settings import *

BOT_NAME = 'hpcloud'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['hpcloud.spiders']
NEWSPIDER_MODULE = 'hpcloud.spiders'


# server reports period set on server side
# so we need to wait and make in sequentially
DOWNLOAD_DELAY = 0.25
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1



ITEM_PIPELINES = [
        'hpcloud.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]


REGIONS = (
        'a-geo-1',
        'a-geo-2'
        )
ZONES = (
        'az-1',
        'az-2',
        'az-3',
)

URLS = dict(
        _LOGIN_URL = (
            'https://console.hpcloud.com/login'
            ),
        _BILLS_URL = (
            'https://account.hpcloud.com/invoices'
          ),
        _SERVERS_URL = 'https://console.hpcloud.com/compute/{zone}_region-{region}/servers.json',
        _FILES_URL = 'https://console.hpcloud.com/object_store/region-{region}/containers',
        )

