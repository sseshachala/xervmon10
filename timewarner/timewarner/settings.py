# Scrapy settings for comcast project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
from basecrawler.base_settings import *

BOT_NAME = 'timewarner'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['timewarner.spiders']
NEWSPIDER_MODULE = 'timewarner.spiders'
# server reports period set on server side
# so we need to wait and make in sequentially
DOWNLOAD_DELAY = 0.25
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1


ITEM_PIPELINES = [
        'timewarner.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]

URLS = dict(
        _LOGIN_URL = (
            'https://customerportal.twtelecom.com/MyBilling/Reports.aspx'
            ),
        _BILLS_URL = (
            'https://customerportal.twtelecom.com/MyBilling/Reports.aspx'),
        _DOWNLOAD_URL = ('https://billing.twtelecom.com/'),
        _CUR_BILL = (
            'https://customerportal.twtelecom.com/MyBilling/MyBilling.aspx')
        )

