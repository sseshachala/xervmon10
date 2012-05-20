# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

class AmazonAccount(Item):
    account_id = Field()

class AmazonCharges(Item):
    _collection_name = "amazonprices"
    _mongo_keys = ['cloud_account_id', 'service', 'startdate', 'enddate', 'cost']
    service = Field()
    cloud_account_id = Field()
    cost = Field()
    link = Field()
    timestamp = Field()
    startdate = Field()
    enddate = Field()

    def get_mongo_obj(self):
        it = {}
        for k in self._mongo_keys:
            it[k] = self.get(k)
        return it



class AmazonUsage(Item):
    _collection_name = "amazon"
    _mongo_keys = [
            "cloud_account_id",
            "service",
            "operation",
            "usagetype",
            "usagevalue",
            "starttime",
            "endtime"
            ]

    service = Field()
    operation = Field()
    usagetype = Field()
    cloud_account_id = Field()
    starttime = Field()
    endtime = Field()
    usagevalue = Field()

    def get_mongo_obj(self):
        it = {}
        for k in self._mongo_keys:
            it[k] = self.get(k)
        return it
