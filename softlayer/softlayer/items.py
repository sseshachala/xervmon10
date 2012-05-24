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


class SoftlayerInvoice(MongoItem):
    _collection_name = 'softlayer_invoices'
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "startdate",
            "enddate",
            "cost",
            "invoice_id",
            "invoice_type"
            ]


class SoftlayerAccount(Item):
    account_id = Field()

class SoftlayerBandwidth(Item):
    server_name = Field()
    bandwidth_current = Field()
    bandwidth_projected = Field()
    allocated = Field()
    ip = Field()


class SoftlayerUsage(MongoItem):
    _collection_name = "softlayer_data"
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "invoice_id",
            "name",
            "cost",
            "startdate",
            "enddate",
            "spec",
            "usage"
            ]


