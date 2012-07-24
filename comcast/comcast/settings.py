# Scrapy settings for comcast project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
from basecrawler.base_settings import *

BOT_NAME = 'comcast'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['comcast.spiders']
NEWSPIDER_MODULE = 'comcast.spiders'

DOWNLOAD_DELAY = 1


ITEM_PIPELINES = [
        'comcast.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]


URLS = dict(
        _LOGIN_URL = (
            'https://login.comcast.net/login'
            ),
        _BILLS_URL = (
            'https://customer.comcast.com/Secure/Account.aspx')
        )

