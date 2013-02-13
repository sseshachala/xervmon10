#!/usr/bin/env python

import datetime
from dateutil.relativedelta import relativedelta


from scrapy.conf import settings
from scrapy import log
from myrack.items import *
from basecrawler.pipelines import BaseMongoDBPipeline, Users, Base, engine



class MongoDBPipeline(BaseMongoDBPipeline):
    def __init__(self):
        super(MongoDBPipeline, self).__init__()
        # List of servers with info 
        self.current = None
        self.invoices = []
        self.old_invoices = []
        self.account_id = None

    def process_item(self, item, spider):
        if isinstance(item, RackCurrent):
            self.current = item.get_mongo_obj()
            return item

        elif isinstance(item, RackInvoice):
            item['cloud_account_id'] = self.user_id
            obj = item.get_mongo_obj()
            self.invoices.append(obj)
            return item

    def open_spider(self, spider):
        res = super(MongoDBPipeline, self).open_spider(spider)
        if not res:
            return
        if not self.account_id:
            log.msg('No account id')
            spiders.errors.append("No account id")
            spider.close_down = True
            return


        spider.username = self.username
        spider.password = self.password
        spider.account_id = self.account_id
        self.ensure_index(RackCurrent)
        self.ensure_index(RackInvoice)
        old_invoices = [i for i in
                self.mongodb[RackInvoice._collection_name].find(
                    dict(
                        cloud_account_id=self.user_id,
                        account_id=self.account_id
                    ))]
        spider.old_invoices = [i['invoice_id'] for i in old_invoices]
    def close_spider(self, spider):
        res = super(MongoDBPipeline, self).close_spider(spider)
        if not res:
            return
        self._write_to_mongo(self.invoices, RackInvoice._collection_name)

class UserStorage(Base):
    __tablename__ = "user_storage_providers"
    __table_args__ = {"autoload": True}


class UserCloud(Base):
    __tablename__ = "user_cloud_providers"
    __table_args__ = {"autoload": True}


Base.metadata.create_all(engine)
