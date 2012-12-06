#!/usr/bin/env python

import datetime
from scrapy.conf import settings
from scrapy import log
from amazon.items import AmazonCharges, AmazonAccount, AmazonInvoice
from basecrawler.pipelines import BaseMongoDBPipeline, Users



class MongoDBPipeline(BaseMongoDBPipeline):
    def __init__(self):
        super(MongoDBPipeline, self).__init__()
        self.service_map = settings['SERVICE_MAP']
        self.amazon_prices = []
        self.acharges = []
        self.ausage = []
        self.account_id = None
        self.old_usage = []
        self.old_charges = []
        self.iam = False
        self.invoices = []
        self.cur_invoices = []

    def process_item(self, item, spider):
        if not self.got_acid and isinstance(item, AmazonAccount):
            self.account_id = item['account_id']
            self._update_account_id()

        elif isinstance(item, AmazonCharges):
            service_name = item['service']
            item['service'] = self.service_map.get(service_name, service_name)
            item['cloud_account_id'] = self.user_id
            item['account_id'] = self.account_id
            item['iscurrent'] = False
            obj = item.get_mongo_obj()
            self.cur_invoices.append(obj)

        return item

    def open_spider(self, spider):
        res = super(MongoDBPipeline, self).open_spider(spider)
        if not res:
            return

        spider.iam = self.iam
        spider.user_id = self.user_id
        spider.account_id = self.account_id
        spider.username = self.username
        spider.password = self.password
        fields = ['cloud_account_id', 'startdate', 'enddate', 'iscurrent', 'account_id']
        self.ensure_index(AmazonCharges)
        invcurs = self.mongodb[AmazonCharges._collection_name].find(
                dict(cloud_account_id=self.user_id, iscurrent=False, account_id=self.account_id))
        spider.invoices = [k['startdate'] for k in invcurs]

    def close_spider(self, spider):
        res = super(MongoDBPipeline, self).close_spider(spider)
        if not res:
            return
        new_invoices = []
        # for inv in self.cur_invoices:
        #     invoice = AmazonInvoice()
        #     invoice['services'] = self.cur_invoices[inv]
        #     ex = invoice['services'][0]
        #     invoice['startdate'] = ex['startdate']
        #     invoice['enddate'] = ex['enddate']
        #     invoice['cloud_account_id'] = self.user_id
        #     invoice['account_id'] = self.account_id
        #     invoice['iscurrent'] = False
        #     invoice['cost'] = sum(map(lambda x: x['cost'],
        #         invoice['services']))
        #     new_invoices.append(invoice.get_mongo_obj())
        new_invoices = self.cur_invoices
        if not new_invoices:
            return

        if spider.name == 'aws_current':
            invoices = []
            now = datetime.datetime.now()
            for cur_invoice in new_invoices:
                cur_invoice['iscurrent'] = True
                cur_invoice['added'] = now
                invoices.append(cur_invoice)
            self.mongodb[AmazonCharges._collection_name].remove(dict(
                cloud_account_id=cur_invoice['cloud_account_id'],
                account_id=cur_invoice['account_id'],
                iscurrent=True
                ))
            self._write_to_mongo(invoices, AmazonCharges._collection_name)
            self._write_to_mongo(invoices, settings['INVOICES_ANALYTICS'])
        elif spider.name == 'aws_hist':
            self._write_to_mongo(new_invoices, AmazonCharges._collection_name)


    def _get_credentials(self):
        user = super(MongoDBPipeline, self)._get_credentials()
        if not user:
            return None
        cred_type = user.credential_type
        if cred_type == 'IAM':
            self.iam = True
        else:
            self.iam = False
        return user
