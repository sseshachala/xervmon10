from scrapy.item import Item, Field
from basecrawler.items import MongoItem

class RackAccount(Item):
    account_id = Field()


class RackService(Item):
    name = Field()
    total_number = Field()


class RackCurrent(MongoItem):
    _collection_name = "mycloudrack_current"
    enddate = Field()
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "last_updated",
            "services",
            ]

class RackInvoice(MongoItem):
    _collection_name = "mycloudrack_data"
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "startdate",
            "enddate",
            "total",
            "invoice_id",
            "services"
            ]
