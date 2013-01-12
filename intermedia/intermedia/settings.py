from basecrawler.base_settings import *

BOT_NAME = 'intermedia'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['intermedia.spiders']
NEWSPIDER_MODULE = 'intermedia.spiders'


# ITEM_PIPELINES = [
#         'intermedia.pipelines.MongoDBPipeline',
#         'basecrawler.pipelines.StatusPipeline'
#         ]


URLS = dict(
        _URL_LOGIN = "https://exchange.intermedia.net/aspx/Login.aspx",
        _URL_INVOICES = "https://exchange.intermedia.net/asp/User/Account/Billing/AccountBalances.asp",
        _URL_ACCOUNT = 'https://exchange.intermedia.net/aspx/User/Account/Account.aspx'
        )
SPIDER_MIDDLEWARES = {}
DOWNLOADER_MIDDLEWARES = {}
EXTENSIONS = {}

