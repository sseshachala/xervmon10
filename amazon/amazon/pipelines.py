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
        if not self.user_id:
            log.msg('No user id')
            spider.close_down = True
            return

        u, p, self.got_acid = self._get_credentials()
        spider.iam = self.iam
        spider.user_id = self.user_id
        spider.account_id = self.account_id
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
        spider.username = u
        spider.password = p

    def close_spider(self, spider):
        if spider.close_down or not self.account_id or not self.user_id:
            return
        basecharges = [d for d in self.mongodb[AmazonCharges._collection_name].find(dict(cloud_account_id=self.user_id))]
        usage = []
        charges = []
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
        user = self.session.query(Users).filter_by(id=self.user_id).first()
        if not user:
            return (None, None, False)
        cred_type = user.credential_type
        password = self._decrypt_password(user.password)
        self.account_id = user.account_id
        if cred_type == 'IAM':
            self.iam = True
        else:
            self.iam = False
        return (user.account_user, user.password, user.account_id != "")
