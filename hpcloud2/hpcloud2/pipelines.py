#!/usr/bin/env python

import datetime

from scrapy.conf import settings
from scrapy import log
from hpcloud2.items import *

from basecrawler.pipelines import BaseMongoDBPipeline


class MongoDBPipeline(BaseMongoDBPipeline):
    def __init__(self):
        super(MongoDBPipeline, self).__init__()
        # List of servers with info 
        log.msg('host is')
        log.msg(settings.get('MONGO_HOST'))
        self.account_id = None
        self.got_acid = False
        # From mongodb
        self.sbills = []
        self.comcurrent = None
        self.old_bills = []

    def process_item(self, item, spider):
        if not self.account_id and isinstance(item, HPCloudAccount):
            self.account_id = item['account_id']
            self._update_account_id()

        elif isinstance(item, HPCloudData):
            item['cloud_account_id'] = self.user_id
            item['account_id'] = self.account_id
            obj = item.get_mongo_obj()
            self.sbills.append(obj)
            for service in item['services'].keys():
                if not service in spider.new_services:
                    spider.new_services.append(service)

        elif isinstance(item, HPCloudCurrent):
            item['cloud_account_id'] = self.user_id
            item['account_id'] = self.account_id
            obj = item.get_mongo_obj()
            self.comcurrent = obj

        return item

    def open_spider(self, spider):
        res = super(MongoDBPipeline, self).open_spider(spider)
        if not res:
            return

        spider.username = self.username
        spider.password = self.password
        now = datetime.datetime.now()
        self.ensure_index(HPCloudData)
        if self.got_acid:
            old_bills = [i for i in
                self.mongodb[HPCloudData._collection_name].find(
                    dict(
                        cloud_account_id=str(self.user_id),
                        account_id=self.account_id
                    ))]
            spider.invoices = [i['invoice_number'] for i in old_bills]
            log.msg("Old invoices %s" % spider.invoices)

    def close_spider(self, spider):
        res = super(MongoDBPipeline, self).close_spider(spider)
        if not res:
            return

        self._write_to_mongo(self.sbills, HPCloudData._collection_name)
        if self.comcurrent:
            prev = self.mongodb[HPCloudCurrent._collection_name].remove(
                dict(
                    cloud_account_id=str(self.user_id),
                    account_id=self.account_id
                ))
            self.mongodb[HPCloudCurrent._collection_name].insert(self.comcurrent)
