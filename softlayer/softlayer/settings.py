# Scrapy settings for softlayer project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
from basecrawler.base_settings import *

BOT_NAME = 'softlayer'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['softlayer.spiders']
NEWSPIDER_MODULE = 'softlayer.spiders'

DOWNLOAD_DELAY = 0.2



ITEM_PIPELINES = [
        'softlayer.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]

URLS = dict(
    _BILLING_URL = "https://manage.softlayer.com/Administrative/accountSummary",

    _URL_NEXT_INVOICE = "https://manage.softlayer.com/Administrative/showNextInvoice",
    _URL_NEXT_INVOICE_XLS = "https://manage.softlayer.com/Administrative/showNextInvoice/xls",
    FORM_URL = (
    'https://manage.softlayer.com/Administrative/accountSummarySL/tabView'),
    _URL_BANDWIDTH = 'https://manage.softlayer.com/PublicNetwork/bandwidth'
)
