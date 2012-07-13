#!/usr/bin/env python

import datetime

from scrapy.conf import settings
from scrapy import log
from att.items import *
from basecrawler.pipelines import BaseMongoDBPipeline




class MongoDBPipeline(BaseMongoDBPipeline):
    def __init__(self):
        super(MongoDBPipeline, self).__init__()
        # List of servers with info 
        self.account_id = None
        # From mongodb
        self.sbills = []
        self.old_bills = []

    def process_item(self, item, spider):
        if not self.account_id and isinstance(item, AttAccount):
            self.account_id = item['account_id']
            self._update_account_id()

        elif isinstance(item, AttBill):
            item['cloud_account_id'] = self.user_id
            item['account_id'] = self.account_id
            obj = item.get_mongo_obj()
            self.sbills.append(obj)

        return item
    def close_spider(self, spider):
        res = super(MongoDBPipeline, self).close_spider(spider)
        if not res:
            return
        self._write_to_mongo(self.sbills, AttBill._collection_name)

    def open_spider(self, spider):
        res = super(MongoDBPipeline, self).open_spider(spider)
        if not res:
            return

        spider.username = self.username
        spider.password = self.password
        now = datetime.datetime.now()
        self.ensure_index(AttBill)
        if self.got_acid:
            old_bills = [i for i in
                self.mongodb[AttBill._collection_name].find(
                    dict(
                        cloud_account_id=str(self.user_id),
                        account_id=self.account_id
                    ))]
            spider.invoices = [i[u'enddate'].strftime('%Y%m%d') for i in old_bills if isinstance(i[u'enddate'], type(now))]
            log.msg("Old invoices %s" % spider.invoices)

