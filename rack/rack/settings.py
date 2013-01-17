# Scrapy settings for rack project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
from basecrawler.base_settings import *

BOT_NAME = 'rack'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['rack.spiders']
NEWSPIDER_MODULE = 'rack.spiders'


ITEM_PIPELINES = [
        'rack.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]


BASE_URL = "https://manage.rackspacecloud.com"
URLS = dict(

    _URL_LOGIN = "/pages/Login.jsp",
    _URL_SERVERS = "/CloudServers/ServerList.do",
    _URL_REPORTS = "/ReportsHome.do",
    _URL_BILLING = "/BillingOverview.do",
    _URL_CURRENT_PRICE = "/CurrentInvoice.do",
    _URL_BILLING_HISTORY = "/BillingHistory.do",
    _URL_CLOUDFILES_CUR = "/CloudFiles/UsageTable.do",
    _URL_LOADBALANCERS_CUR = "/LoadBalancers/UsageTable.do",
    _URL_CLOUDSERVERS_CUR = "/CloudServers/UsageTable.do",
    _URL_INVOICE = "/ViewInvoice.do?invoiceID=",
    _URL_API_KEY = "/APIAccess.do?_jajaxCall=revealApiAccessKey"
        )
