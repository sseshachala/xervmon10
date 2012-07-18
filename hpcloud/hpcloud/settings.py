# Scrapy settings for comcast project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'hpcloud'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['hpcloud.spiders']
NEWSPIDER_MODULE = 'hpcloud.spiders'
USER_AGENT = '%s/%s' % (BOT_NAME, BOT_VERSION)

USER_AGENT = '''Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.162 Safari/535.19'''

# server reports period set on server side
# so we need to wait and make in sequentially
DOWNLOAD_DELAY = 0.25
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1


MONGO_DB = 'xervmon_remote'
MONGO_USER = 'xervmon_remote'
MONGO_PASSWORD = 'xervmonremote'
MONGO_PORT = '27017'
MONGO_IP = '184.106.197.102'
MONGO_HOST = 'mongodb://%s:%s@%s:%s/%s' % (MONGO_USER, MONGO_PASSWORD, MONGO_IP,
                             MONGO_PORT, MONGO_DB)

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

SPIDER_MIDDLEWARES = {
        'basecrawler.middlewares.ErrorsMiddleware': 100
        }
ITEM_PIPELINES = [
        'hpcloud.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]
EXTENSIONS = {
	'scrapy.contrib.feedexport.FeedExporter': None,
}

MONGO_LOG = 'scrape_log'
# CAPTCHA_KEY = '4fe73c77a83c95a2c6fe146c509dfe88'

URLS = dict(
        _LOGIN_URL = (
            'https://console.hpcloud.com/login'
            ),
        _BILLS_URL = (
            'https://console.hpcloud.com/invoices'),
        )

