#!/usr/bin/env python

import datetime
import os.path
from dateutil.relativedelta import relativedelta


from scrapy.conf import settings
from scrapy import log
from rack.items import *
from basecrawler.pipelines import BaseMongoDBPipeline, Users, Base, engine



class MongoDBPipeline(BaseMongoDBPipeline):
    def __init__(self):
        super(MongoDBPipeline, self).__init__()
        # All rackservers data
        self.rservers = []
        # All rackusage data
        self.rusage = []
        # List of servers with info 
        self.newserv = []
        self.totalusagedata = []
        self.totalusage = None
        self.account_id = None
        # From mongodb
        self.old_usage = []
        self.old_invoices = []

    def process_item(self, item, spider):
        if isinstance(item, RackAccount):
            self.account_id = item['account_id']
            if not self.got_acid:
                self._update_account_id()
            return item

        if isinstance(item, RackServerInfo):
            self.newserv.append(item)
            return item

        if isinstance(item, RackTotalUsage):
            item['cloud_account_id'] = self.user_id
            self.totalusage = item
            return item

        if isinstance(item, RackTotalUsageEntry):
            self.totalusagedata.append(item['usage'])
            return item

        if isinstance(item, RackApiKey):
            if not item['key']:
                return
            self._write_key(item['key'])
            return item

        if isinstance(item, RackServers):
            item['cloud_account_id'] = self.user_id
            obj = item.get_mongo_obj()
            if obj in self.old_invoices:
                return
            self.rservers.append(item)
            return item

        if isinstance(item, RackUsage):
            item['cloud_account_id'] = self.user_id
            obj = item.get_mongo_obj()
            service = item['usagetype']
            if service and not service in spider.new_services:
                spider.new_services.append(service)
            if obj in self.old_usage:
                return
            self.rusage.append(item)

    def open_spider(self, spider):
        res = super(MongoDBPipeline, self).open_spider(spider)
        if not res:
            return

        spider.username = self.username
        spider.password = self.password
        self.ensure_index(RackUsage)
        self.ensure_index(RackServers)
        old_invoices = [i for i in
                self.mongodb[RackServers._collection_name].find(
                    dict(
                        cloud_account_id=self.user_id,
                        invoice_id={"$exists": True, "$ne": ""},
                        enddate={"$exists": True}
                    ))]
        spider.old_invoices = [i['invoice_id'] for i in old_invoices]
        urls = settings.get('URLS')
        base_url = settings.get('BASE_URL')
        if self.base_url is None:
            self.base_url = base_url
        for attr, url in urls.items():
            setattr(spider, attr, os.path.join(self.base_url, url))
        spider.start_urls = [spider._URL_LOGIN]


    def close_spider(self, spider):
        res = super(MongoDBPipeline, self).close_spider(spider)
        if not res:
            return
        rusage = []
        rservers = []
        if spider.run_more:
            try:
                self.run_more_spider(spider.run_more)
            except Exception, e:
                log.msg("Couldn run more spider %s. Error %s" % (spider.run_more, str(e)))
        if spider.name == 'rack_current':
            self.mongodb[RackServers._collection_name].remove(dict(
                cloud_account_id = self.user_id,
                account_id = unicode(self.account_id),
                invoice_id = u""
                ))
            if self.totalusage:
                log.msg("Total usage data %s" %
                    str(self.totalusage.get_mongo_obj()))
                self.totalusage['usage'] = self.totalusagedata
                self.totalusage['account_id'] = self.account_id
                self._write_to_mongo([self.totalusage.get_mongo_obj()],
                    RackTotalUsage._collection_name)
            for serv in self.rservers:
                try:
                    s = [d.get_mongo_obj() for d in self.newserv if d['name'] == serv['name']][0]
                    server_info = s
                except:
                    server_info = {'name': serv['name']}
                serv['account_id'] = self.account_id
                serv['server_info'] = server_info
                rservers.append(serv.get_mongo_obj())
            self._write_to_mongo(rservers, RackServers._collection_name)
        if spider.name == 'rack_hist':
            rackinv = []
            rackusage = []
            for r in self.rservers:
                if not 'invoice_id' in r:
                    continue
                q = self.mongodb[RackServers._collection_name].find_one(dict(invoice_id=r['invoice_id'],
                    cloud_account_id=self.user_id))
                if q:
                    continue
                r['account_id'] = self.account_id
                rackinv.append(r.get_mongo_obj())
                for u in self.rusage:
                    if u['invoice_id'] == r['invoice_id']:
                        u['account_id'] = self.account_id
                        rackusage.append(u.get_mongo_obj())
            self._write_to_mongo(rackinv, RackServers._collection_name)
            self._write_to_mongo(rackusage, RackUsage._collection_name)

    def _write_key(self, key):
        if not key or not self.user_id:
            return
        user = self.session.query(Users).filter_by(id=self.user_id).first()
        if not user:
            return
        if user.user_cloud_provider_id or user.user_storage_provider_id:
            return
        cloud_id = user.cloud_provider
        username = user.account_user
        cloud = UserCloud()
        storage = UserStorage()
        cloud.cloud_provider = storage.storage_provider = cloud_id
        cloud.user_id = storage.user_id = self.user_id
        cloud.username = storage.username = username
        cloud.secretkey = storage.secretkey = key
        cloud.active = storage.active = 'yes'
        cloud.api_location = 'US'
        cloud.subscription_id = ''
        cloud.cert_file_path = ''
        cloud.host = ''
        storage.name = ''
        storage.tenant_id = ''
        storage.uri = ''
        self.session.add(cloud)
        self.session.add(storage)
        self.session.flush()
        self.session.refresh(cloud)
        self.session.refresh(storage)

        user.user_cloud_provider_id = cloud.id
        user.user_storage_provider_id = storage.id

        self.session.commit()



class UserStorage(Base):
    __tablename__ = "user_storage_providers"
    __table_args__ = {"autoload": True}


class UserCloud(Base):
    __tablename__ = "user_cloud_providers"
    __table_args__ = {"autoload": True}



Base.metadata.create_all(engine)
