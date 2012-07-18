
from scrapy.item import Item, Field

from basecrawler.items import MongoItem


class HPCloudAccount(Item):
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
            "services"
            ]

