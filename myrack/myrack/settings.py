# Scrapy settings for rack project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
from basecrawler.base_settings import *

BOT_NAME = 'myrack'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['myrack.spiders']
NEWSPIDER_MODULE = 'myrack.spiders'


ITEM_PIPELINES = [
        'myrack.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]

SPIDER_MIDDLEWARES={}
DOWNLOADER_MIDDLEWARES={}

URLS = dict(

        _URL_LOGIN = "https://my.rackspace.com/portal/auth/login?targetUri=%2Fhome",
        _URL_INVOICES = "https://my.rackspace.com/portal/transaction/list?type=invoices",
        )
