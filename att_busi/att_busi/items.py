# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

from basecrawler.items import MongoItem


class AttAccount(Item):
    account_id = Field()

class AttBill(MongoItem):
    _collection_name = "att_business_data"
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "startdate",
            "enddate",
            "service_accounts",
            "account_charges",
            "prior_activity",
            "total_charges",
            "total_amount"
            ]

