from scrapy.item import Item, Field

class RackAccount(Item):
    account_id = Field()

class RackItem(Item):
    _mongo_keys = []

    def get_mongo_obj(self, all_fields=False):
        it = {}
        mongo_keys = self._mongo_keys
        if all_fields:
            mongo_keys = self.keys()
        for i in mongo_keys:
            it[i] = self.get(i)
        return it


class RackServerInfo(RackItem):
    _mongo_keys = ["name", "ip", "id"]
    name = Field()
    ip = Field()
    id = Field()


class RackUsage(RackItem):
    _collection_name = "rackdata"
    enddate = Field()
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "usagetype",
            "cost",
            "enddate",
            "operation",
            "startdate",
            "service",
            "invoice_id",
            "usagevalue"
            ]
    cloud_account_id = Field()
    account_id = Field()
    usagetype = Field()
    cost = Field()
    startdate = Field()
    service = Field()
    enddate = Field()
    operation = Field()
    server = Field()
    invoice_id = Field()
    usagevalue = Field()


class RackServers(RackItem):
    _collection_name = "rackservers"
    _mongo_keys = [
            "cloud_account_id",
            "account_id",
            "invoice_id",
            "server_info",
            "usage",
            "startdate",
            "enddate",
            "cost"
            ]
    cloud_account_id = Field()
    account_id = Field()
    name = Field()
    invoice_id = Field()
    server_info = Field()
    usage = Field()
    startdate = Field()
    enddate = Field()
    c ost = Field()

class RackTotalUsage(RackServers):
    pass

class RackTotalUsageEntry(Item):
    usage = Field()

class RackApiKey(Item):
    key = Field()
    cloud_account_id = Field()
