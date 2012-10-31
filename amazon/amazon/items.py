# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field
from basecrawler.items import MongoItem

class AmazonAccount(Item):
    account_id = Field()

class AmazonCharges(MongoItem):
    _collection_name = "amazon_new_prices"
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            'service',
            'startdate',
            'enddate',
            'cost',
            "iscurrent",
            'usage',
            ]
    link = Field()
    timestamp = Field()


class AmazonUsage(Item):
    _collection_name = "amazon_new"
    _mongo_keys = [
            "cloud_account_id",
            "service",
            "operation",
            "usagetype",
            "usagevalue",
            "starttime",
            "endtime"
            ]

    startdate = Field()

class AmazonInvoice(MongoItem):
    _collection_name = 'amazon_invoice_new'
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "services",
            "startdate",
            "enddate",
            "cost",
            "iscurrent"
            ]
