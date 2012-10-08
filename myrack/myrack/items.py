from scrapy.item import Item, Field
from basecrawler.items import MongoItem

class RackAccount(Item):
    account_id = Field()



class RackCurrent(MongoItem):
    _collection_name = "myrack_current"
    enddate = Field()
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "cost",
            "enddate",
            "startdate",
            "services",
            ]

class RackInvoice(MongoItem):
    _collection_name = "myrack_data"
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "startdate",
            "enddate",
            "total",
            "invoice_id",
            "services"
            ]
