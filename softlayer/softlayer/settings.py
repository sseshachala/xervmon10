# Scrapy settings for softlayer project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'softlayer'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['softlayer.spiders']
NEWSPIDER_MODULE = 'softlayer.spiders'
USER_AGENT = '%s/%s' % (BOT_NAME, BOT_VERSION)

MONGO_DB = 'xervmon_remote'
MONGO_HOST = 'mongodb://%s:%s@%s:%s/%s' % ('xervmon_remote', 'xervmonremote',
    '184.106.197.102', '27017', MONGO_DB)

MYSQL_USER = 'xervmon_remote'
MYSQL_PASSWORD = 'Java23man'
MYSQL_DB = 'controlpanel'
MYSQL_HOST = '184.106.197.102'

USER_ID = None
KEY = 'yDo4V5B0j9V3JRJ4lO55q77Wm5r7dLC8'

SENDER_EMAIL = 'sysadmin@hooduku.com'
SENDER_PASSWORD = 'admin9873%man'
RECEIVER_EMAIL = 'sudhi@hooduku.com'
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = '587'
MONGO_LOG = 'scrape_log'

SPIDER_MIDDLEWARES = {
         'softlayer.middlewares.ErrorsMiddleware': 100
        }

ITEM_PIPELINES = [
        'softlayer.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]

EXTENSIONS = {
	'scrapy.contrib.feedexport.FeedExporter': None,
}
URLS = dict(
    _BILLING_URL = "https://manage.softlayer.com/Administrative/accountSummary",

    _URL_NEXT_INVOICE = "https://manage.softlayer.com/Administrative/showNextInvoice",
    _URL_NEXT_INVOICE_XLS = "https://manage.softlayer.com/Administrative/showNextInvoice/xls",
    FORM_URL = (
    'https://manage.softlayer.com/Administrative/accountSummarySL/tabView'),
    _URL_BANDWIDTH = 'https://manage.softlayer.com/PublicNetwork/bandwidth'
)
