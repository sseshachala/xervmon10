from basecrawler.base_settings import *
BOT_NAME = 'mycloudrack'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['mycloudrack.spiders']
NEWSPIDER_MODULE = 'mycloudrack.spiders'
USER_AGENT = '%s/%s' % (BOT_NAME, BOT_VERSION)


ITEM_PIPELINES = [
        'mycloudrack.pipelines.UrlPipeline',
        'mycloudrack.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]

BASE_URL = "https://mycloud.rackspace.com"
URLS = dict(

    _URL_LOGIN = "/",
    _URL_INVOICES = "/proxy/rax:billing,billing/billing-summary/?limit=100",
    _URL_INVOICE = "/proxy/rax:billing,billing/invoices/",
    _URL_SERVERS_ADD = "/proxy/compute,cloudServersOpenStack,{region}/servers/detail",
    _URL_SERVERS = "/proxy/compute,cloudServers/servers/detail",
    _URL_BALANCER = "/proxy/rax:load-balancer,cloudLoadBalancers,{region}/loadbalancers",
    _URL_DNS = "/proxy/rax:dns,cloudDNS/domains/?offset=0&limit=100",
    _URL_FILES = "/proxy/object-store,cloudFiles,{region}/?limit=100",
    _URL_DATABASE = "/proxy/rax:database,cloudDatabases,{region}/instances",
    _URL_BACKUP = "/ck/sso/backup/",
    _URL_BACKUP_DATA = "https://clouddrive.rackspace.com/services/v1.0/user/agents/"
        )

REGIONS = (
        'DFW',
        'ORD'
        )

SPECIFIC_URLS = {
        "https://mycloud.rackspace.co.uk": {
            }
        }
