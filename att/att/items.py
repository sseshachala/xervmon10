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

class AttAccount(Item):
    account_id = Field()

class AttBill(MongoItem):
    _collection_name = "att_data"
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "startdate",
            "enddate",
            "service_accounts",
            "account_charges",
            "totalcost"
            ]

