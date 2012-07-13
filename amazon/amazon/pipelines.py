#!/usr/bin/env python

import datetime
from scrapy.conf import settings
from scrapy import log
from amazon.items import AmazonCharges, AmazonAccount, AmazonUsage
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

    def process_item(self, item, spider):
        if not self.got_acid and isinstance(item, AmazonAccount):
            self.account_id = item['account_id']
            self._update_account_id()
        elif isinstance(item, AmazonCharges):
            service_name = item['service']
            item['service'] = self.service_map.get(service_name, service_name)
            item['cloud_account_id'] = self.user_id
            obj = item.get_mongo_obj()
            self.acharges.append(obj)
        elif isinstance(item, AmazonUsage):
            item['cloud_account_id'] = self.user_id
            obj = item.get_mongo_obj()
            self.ausage.append(obj)
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
        if spider.iam:
            spider.start_urls = [spider.IAM_LOGIN_URL % self.account_id]
            log.msg("IAM mode with starturl %s" % str(spider.start_urls))
        fields = ['cloud_account_id', 'service', 'startdate', 'enddate']
        self.ensure_index(AmazonCharges)
        self.ensure_index(AmazonUsage)
        invcurs = self.mongodb[AmazonCharges._collection_name].find(dict(cloud_account_id=self.user_id))
        spider.invoices = []
        for inv in invcurs:
            if fields not in inv.keys():
                continue
            spider.invoices.append(dict([(k, inv[k]) for k in inv if k in fields]))

    def close_spider(self, spider):
        res = super(MongoDBPipeline, self).close_spider(spider)
        if not res:
            return
        if spider.name == 'aws_current':
            for it in self.acharges:
                obj = it
                self.mongodb[AmazonCharges._collection_name].update(dict([(o, obj[o]) for o in obj if o != 'cost']), obj, upsert=True)
            for it in self.ausage:
                obj = it
                self.mongodb[AmazonUsage._collection_name].update(dict([(o, obj[o]) for o in obj if o != 'usagevalue']), obj, upsert=True)
        elif spider.name == 'aws_hist':
            self._write_to_mongo(self.ausage, AmazonUsage._collection_name)
            self._write_to_mongo(self.acharges, AmazonCharges._collection_name)


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
