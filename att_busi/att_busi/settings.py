# Scrapy settings for att project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
from basecrawler.base_settings import *

BOT_NAME = 'att_busi'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['att_busi.spiders']
NEWSPIDER_MODULE = 'att_busi.spiders'

DOWNLOAD_DELAY = 1
RECEIVER_EMAIL = 'snoopt@yandex.ru'


ITEM_PIPELINES = [
        #'att_busi.pipelines.MongoDBPipeline',
        # 'basecrawler.pipelines.StatusPipeline'
        ]
MIDDLEWARES = {}
DOWNLOADER_MIDDLEWARES = {}
SPIDER_MIDDLEWARES = {
        }
EXTENSIONS = {
	'scrapy.contrib.feedexport.FeedExporter': None,
        }
URLS = dict(
    _LOGIN_URL = (
        'https://www.businessdirect.att.com/portal/index.jsp'),
    _BILLS_URL = (
        'https://obt.bus.att.com/servlet/ecare?inf_action=ibi_report_view&action_type=reportsMenu'),
    )
