# Scrapy settings for rack project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'rack'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['rack.spiders']
NEWSPIDER_MODULE = 'rack.spiders'
USER_AGENT = '%s/%s' % (BOT_NAME, BOT_VERSION)

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
MONGO_LOG = 'scrape_log'

SPIDER_MIDDLEWARES = {
        'basecrawler.middlewares.ErrorsMiddleware': 100
        }

ITEM_PIPELINES = [
        'rack.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]

EXTENSIONS = {
	'scrapy.contrib.feedexport.FeedExporter': None,
}

URLS = dict(

    _URL_LOGIN = "https://manage.rackspacecloud.com/pages/Login.jsp",
    _URL_SERVERS = "https://manage.rackspacecloud.com/CloudServers/ServerList.do",
    _URL_REPORTS = "https://manage.rackspacecloud.com/ReportsHome.do",
    _URL_BILLING = "https://manage.rackspacecloud.com/BillingOverview.do",
    _URL_CURRENT_PRICE = "https://manage.rackspacecloud.com/CurrentInvoice.do",
    _URL_BILLING_HISTORY = "https://manage.rackspacecloud.com/BillingHistory.do",
    _URL_CLOUDFILES_CUR = "https://manage.rackspacecloud.com/CloudFiles/UsageTable.do",
    _URL_LOADBALANCERS_CUR = "https://manage.rackspacecloud.com/LoadBalancers/UsageTable.do",
    _URL_CLOUDSERVERS_CUR = "https://manage.rackspacecloud.com/CloudServers/UsageTable.do",
    _URL_INVOICE = "https://manage.rackspacecloud.com/ViewInvoice.do?invoiceID=",
    _URL_API_KEY = "https://manage.rackspacecloud.com/APIAccess.do?_jajaxCall=revealApiAccessKey"

        )
