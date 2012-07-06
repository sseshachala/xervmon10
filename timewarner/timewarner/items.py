# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

class MongoItem(Item):
    _mongo_keys = []
    def __init__(self, *args, **kwargs):
        super(MongoItem, self).__init__(*args, **kwargs)
        for k in self._mongo_keys:
            self.fields[k] = {}

    def get_mongo_obj(self):
        it = {}
        for k in self._mongo_keys:
            it[k] = self.get(k)
        return it

class TimewarnerAccount(Item):
    account_id = Field()


class TimewarnerCurrent(MongoItem):
    _collection_name = "timewarner_current"
    _mongo_keys = [
            "startdate",
            "enddate",
            "cloud_account_id",
            "account_id",
            "total",
            "tax"
            ]

class TimewarnerData(MongoItem):
    _collection_name = "timewarner_data"
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "startdate",
            "enddate",
            "total",
            "services"
            ]

