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
