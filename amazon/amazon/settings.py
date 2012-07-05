# Scrapy settings for amazon project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'amazon'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['amazon.spiders']
NEWSPIDER_MODULE = 'amazon.spiders'
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
        'amazon.middlewares.ErrorsMiddleware': 100
        }


ITEM_PIPELINES = [
        'amazon.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]

EXTENSIONS = {
	'scrapy.contrib.feedexport.FeedExporter': None,
}
SERVICE_MAP = {
        "AWS Data Transfer (excluding Amazon CloudFront)": "transfer",
        "AWS Import/Export": "IngestionService",
        "AWS Storage Gateway": "AWSStorageGateway",
        "Amazon CloudFront": "AmazonCloudFront",
        "Amazon CloudWatch": "CLOUDWATCH",
        "Amazon DynamoDB": "AmazonDynamoDB",
        "Amazon ElastiCache": "AmazonElastiCache",
        "Amazon Elastic Compute Cloud": "AmazonEC2",
        "Amazon Elastic MapReduce": "ElasticMapReduce",
        "Amazon RDS Service": "AmazonRDS",
        "Amazon Route 53": "AmazonRoute53",
        "Amazon Simple Notification Service": "AmazonSNS",
        "Amazon Simple Queue Service": "AWSQueueService",
        "Amazon Simple Storage Service": "AmazonS3",
        "Amazon Simple Workflow Service": "AmazonSWF",
        "Amazon SimpleDB": "AmazonSimpleDB",
        "Amazon Virtual Private Cloud": "AmazonVPC"
        }

URLS = dict(
    _ACCOUNT_SUMMARY_URL = "https://aws-portal.amazon.com/gp/aws/developer/account/index.html?ie=UTF8&action=activity-summary",
    IAM_LOGIN_URL = 'https://%s.signin.aws.amazon.com/console'

        )
