#!/usr/bin/env python

import datetime

from scrapy.conf import settings
from scrapy import log
from softlayer.items import *
from basecrawler.pipelines import BaseMongoDBPipeline




class MongoDBPipeline(BaseMongoDBPipeline):
    CURRENT_INVOICE = u'0000000000'

    def __init__(self):
        super(MongoDBPipeline, self).__init__()
        self.sinvoices = []
        self.susage = []
        self.sbandwidth = []
        # List of servers with info 
        self.account_id = None
        self.got_acid = False
        # From mongodb
        self.old_usage = []
        self.old_invoices = []

    def process_item(self, item, spider):
        if not self.account_id and isinstance(item, SoftlayerAccount):
            self.account_id = item['account_id']
            self._update_account_id()

        elif isinstance(item, SoftlayerInvoice):
            item['cloud_account_id'] = self.user_id
            item['account_id'] = self.account_id
            obj = item.get_mongo_obj()
            self.sinvoices.append(obj)
        elif isinstance(item, SoftlayerBandwidth):
            if item['server_name']:
                self.sbandwidth.append(item)

        elif isinstance(item, SoftlayerUsage):
            item['account_id'] = self.account_id
            item['cloud_account_id'] = self.user_id
            for spec in item['spec']:
                service = spec['name']
                if service and not service in spider.new_services:
                    spider.new_services.append(service)
            obj = item.get_mongo_obj()
            self.susage.append(obj)
        return item

    def open_spider(self, spider):
        res = super(MongoDBPipeline, self).open_spider(spider)
        if not res:
            return

        spider.username = self.username
        spider.password = self.password
        self.ensure_index(SoftlayerInvoice)
        self.ensure_index(SoftlayerUsage)
        if self.got_acid:
            old_invoices = [i for i in
                self.mongodb[SoftlayerInvoice._collection_name].find(
                    dict(
                        cloud_account_id=str(self.user_id),
                        account_id=self.account_id,
                        invoice_id={"$exists": True, "$ne":
                            self.CURRENT_INVOICE}
                    ))]
            spider.invoices = [i[u'invoice_id'] for i in old_invoices]
            log.msg("Old invoices %s" % spider.invoices)

    def close_spider(self, spider):
        res = super(MongoDBPipeline, self).close_spider(spider)
        if not res:
            return
        if spider.name == 'softlayer_current':
            self.mongodb[SoftlayerUsage._collection_name].remove(
                    dict(cloud_account_id=self.user_id, invoice_id=self.CURRENT_INVOICE))
            self.mongodb[SoftlayerInvoice._collection_name].remove(
                    dict(cloud_account_id=self.user_id, invoice_id=self.CURRENT_INVOICE))

            for band in self.sbandwidth:
                for use in self.susage:
                    if band['server_name'] in use['name']:
                        if not isinstance(use['usage'], list):
                            use['usage'] = []
                        use['usage'].append(band.get_mongo_obj())
                        break

        self._write_to_mongo(self.sinvoices, SoftlayerInvoice._collection_name)
        self._write_to_mongo(self.susage, SoftlayerUsage._collection_name)


