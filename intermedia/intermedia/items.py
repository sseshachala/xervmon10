from scrapy.item import Item, Field
from basecrawler.items import MongoItem

class IntermediaAccount(Item):
    account_id = Field()


class IntermediaCurrent(MongoItem):
    _collection_name = "intermedia_current"
    enddate = Field()
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "cost",
            "enddate",
            "startdate",
            "services",
            ]

class IntermediaInvoice(MongoItem):
    _collection_name = "intermedia_data"
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "startdate",
            "enddate",
            "total",
            "invoice_id",
            "services"
            ]
