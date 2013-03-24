from basecrawler.base_settings import *
BOT_NAME = 'mycloudrack'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['mycloudrack.spiders']
NEWSPIDER_MODULE = 'mycloudrack.spiders'
USER_AGENT = '%s/%s' % (BOT_NAME, BOT_VERSION)


ITEM_PIPELINES = [
        'mycloudrack.tmp_pipelines.UrlPipeline',
        # 'mycloudrack.pipelines.MongoDBPipeline',
        # 'basecrawler.pipelines.StatusPipeline'
        ]
EXTENSIONS = {}

BASE_URL = "https://mycloud.rackspace.com"
URLS = dict(

    _URL_LOGIN = "/",
    _URL_INVOICES = "/proxy/rax:billing,billing/billing-summary/",
    _URL_INVOICE = "/proxy/rax:billing,billing/invoices/",
    _URL_SERVERS = "/proxy/compute,cloudServersOpenStack,{region}/servers/detail",
    _URL_BALANCER = "/proxy/rax:load-balancer,cloudLoadBalancers,{region}/loadbalancers",
    _URL_DNS = "/proxy/rax:dns,cloudDNS/domains/",
    _URL_FILES = "/proxy/object-store,cloudFiles,{region}/",
    _URL_DATABASE = "/proxy/rax:database,cloudDatabases,{region}/instances",
    _URL_BACKUP = "/services/v1.0/user/agents/"
        )

REGIONS = (
        'DFW',
        'ORD'
        )

SPECIFIC_URLS = {
        "https://mycloud.rackspace.co.uk": {
            }
        }
