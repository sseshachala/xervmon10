# Scrapy settings for amazon project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
from basecrawler.base_settings import *

BOT_NAME = 'amazon'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['amazon.spiders']
NEWSPIDER_MODULE = 'amazon.spiders'

ITEM_PIPELINES = [
        'amazon.pipelines.MongoDBPipeline',
        'basecrawler.pipelines.StatusPipeline'
        ]

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
DOWNLOADER_MIDDLEWARES = {}
SPIDER_MIDDLEWARES = {}
MYSQL_USER = 'xervmon_user'
MYSQL_PASSWORD = 'xervmon2763man'
MYSQL_DB = 'xervmon_prod'
MONGO_DB = 'xervmon_qa'
USER_ID = '339'
RECEIVER_EMAIL = 'snoopt@yandex.ru'
