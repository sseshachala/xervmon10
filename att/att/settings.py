# Scrapy settings for att project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'att'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['att.spiders']
NEWSPIDER_MODULE = 'att.spiders'
USER_AGENT = '''Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.162 Safari/535.19'''

DOWNLOAD_DELAY = 1


MONGO_DB = 'xervmon_remote'
MONGO_HOST = 'mongodb://%s:%s@%s:%s/%s' % ('xervmon_remote', 'xervmonremote',
    '184.106.197.102', '27017', MONGO_DB)

MYSQL_USER = 'xervmon_remote'
MYSQL_PASSWORD = 'Java23man'
MYSQL_DB = 'controlpanel'
MYSQL_HOST = '184.106.197.102'

USER_ID = None

SENDER_EMAIL = 'sysadmin@hooduku.com'
SENDER_PASSWORD = 'admin9873%man'
RECEIVER_EMAIL = 'sudhi@hooduku.com'
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = '587'
MONGO_LOG = 'scrape_log'

ITEM_PIPELINES = [
        'att.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]
EXTENSIONS = {
	'scrapy.contrib.feedexport.FeedExporter': None,
}
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
