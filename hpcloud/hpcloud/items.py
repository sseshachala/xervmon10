# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html
#from __future__ import absolute_import

from scrapy.item import Item, Field

from basecrawler.items import MongoItem

class HPCloudAccount(Item):
    account_id = Field()

class Hpcloud2Item(Item):
    account_id = Field()

class HPCloudCurrent(MongoItem):
    _collection_name = "hpcloud_current"
    _mongo_keys = [
            "startdate",
            "enddate",
            "cloud_account_id",
            "account_id",
            "total",
            "tax"
            ]

class HPCloudData(MongoItem):
    _collection_name = "hpcloud_data"
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "startdate",
            "enddate",
            "total",
            "services",
            "totals",
            "invoice_number"
            ]

