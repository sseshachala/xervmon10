# Scrapy settings for att project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
from basecrawler.base_settings import *

BOT_NAME = 'att'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['att.spiders']
NEWSPIDER_MODULE = 'att.spiders'
USER_AGENT = '''Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.162 Safari/535.19'''

DOWNLOAD_DELAY = 1


ITEM_PIPELINES = [
        'att.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]
URLS = dict(
    _BASE_URL = ('https://www.att.com/'),
    _LOGIN_URL = (
        'https://www.att.com/olam/loginAction.olamexecute?customerType=W'),
    _DETAIL_URL = (
        'https://www.att.com/olam/passthroughAction.myworld?actionType=ViewBillDetails'),
    _BILLS_URL = (
            'https://www.att.com/olam/passthroughAction.myworld?actionType=ViewBillHistory'),
    _LAST_BILL_URL = (
            'https://www.att.com/view/billSummary.doview')
    )
