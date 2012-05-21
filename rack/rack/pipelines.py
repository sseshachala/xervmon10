#!/usr/bin/env python

import pymongo
import csv
import datetime
from dateutil.relativedelta import relativedelta
import smtplib
import StringIO
import urllib2
from urllib import urlencode

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scrapy.conf import settings
from scrapy import log
from rack.items import *

connect_str = 'mysql+mysqldb://%s:%s@%s/%s' % (settings['MYSQL_USER'],
        settings['MYSQL_PASSWORD'], settings['MYSQL_HOST'], settings['MYSQL_DB'])
engine = create_engine(connect_str, echo=False)
Base = declarative_base()
SqliteSession = sessionmaker(bind=engine)
SESSION = SqliteSession()
Base.metadata.bind = engine
MONGO_CONN = pymongo.Connection(settings.get('MONGO_HOST'))

LOGCOL = settings.get("MONGO_LOG")


class StatusPipeline(object):
    def __init__(self):
        self.mongodb = MONGO_CONN[settings['MONGO_DB']]
        self.user_id = settings.get('USER_ID')
        self.session = SESSION
        self.sender_email = settings.get("SENDER_EMAIL")
        self.sender_password = settings.get("SENDER_PASSWORD")
        self.receiver_email = settings.get("RECEIVER_EMAIL")
        self.smtp_host = settings.get("SMTP_HOST")
        self.smtp_port = settings.get("SMTP_PORT")

    def open_spider(self, spider):
        status = "Working"
        cmd = spider.name
        self.log(status, cmd)

    def close_spider(self, spider):
        log.msg(spider)
        cmd = spider.name
        e = ''
        if spider.close_down:
            spider.errors.append('Login error')
        if spider.errors:
            status = 'Error'
            e = ' \n'.join(spider.errors)
        else:
            status = 'Success'
        self.log(status, cmd, e)
        self.email(status, cmd, e)

    def log(self, status, cmd, error=''):
        now = datetime.datetime.now()
        prevday = now - datetime.timedelta(days=1)
        user = self.session.query(Users).filter_by(id=self.user_id).first()
        if user:
            user.login_status = status
            user.login_log = error
            self.session.commit()
        self.mongodb[LOGCOL].remove({"cloud_account_id": self.user_id, "script": cmd, "added": { "$gt": prevday}})
        self.mongodb[LOGCOL].insert({"cloud_account_id": self.user_id, "status": status, "traceback": error,
            "script": cmd, "added": now})


    def email(self, status, cmd, e=''):
        if not self.user_id:
            return
        header = 'To:%s\r\nFrom:%s\r\nSubject:Status=%s for cmd %s\r\n\r\n' % (
                       self.receiver_email, self.sender_email, status, cmd)

        msg = header
        user = self.session.query(Users).filter_by(id=self.user_id).first()
        for k, v in user.__dict__.items():
            if k.startswith('_') or (k == 'password'):
                continue
            msg += '%s: %s\n' % (k, v)
        if e:
            msg += 'Traceback: %s' % e
        smail = smtplib.SMTP(self.smtp_host, self.smtp_port)
        smail.ehlo()
        smail.starttls()
        smail.ehlo()
        smail.login(self.sender_email, self.sender_password)
        smail.sendmail(self.sender_email, self.receiver_email, msg)
        smail.quit()


class MongoDBPipeline(object):
    def __init__(self):
        log.msg(settings.get('MONGO_HOST'))
        self.mongodb = MONGO_CONN[settings['MONGO_DB']]
        self.user_id = settings.get('USER_ID')
        log.msg('User id is %s' % self.user_id)
        # All rackservers data
        self.rservers = []
        # All rackusage data
        self.rusage = []
        # List of servers with info 
        self.newserv = []
        self.totalusagedata = []
        self.totalusage = None
        self.account_id = None
        self.got_acid = False
        # From mongodb
        self.old_usage = []
        self.old_invoices = []
        # sqlalchemy session
        self.session = SESSION

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
            if obj in self.old_usage:
                return
            self.rusage.append(item)

    def open_spider(self, spider):
        # check userid and credentials
        if not self.user_id:
            log.msg('No user id')
            spider.close_down = True
            return

        u, p, self.got_acid = self._get_credentials()
        if not u or not p:
            log.msg('No login or password')
            spider.close_down = True
            return
        spider.username = u
        spider.password = p
        old_invoices = [i for i in
                self.mongodb[RackServers._collection_name].find(
                    dict(
                        cloud_account_id=self.user_id,
                        invoice_id={"$exists": True, "$ne": ""},
                        enddate={"$exists": True}
                    ))]
        spider.old_invoices = [i['invoice_id'] for i in old_invoices]
        if spider.name != 'rack_current' or not spider.old_invoices:
            return
        filtered_inv = sorted(old_invoices, key=lambda k: k['enddate'],
                reverse=True)
        try:
            last_inv = filtered_inv[0]
        except IndexError:
            last_inv = None
        now = datetime.datetime.now()
        if last_inv and isinstance(last_inv['enddate'], type(now)):
            last_date = last_inv['enddate'] + relativedelta(months=+1)
            if last_date < now:
                log.msg("Date of last invoce more than a month")
                self.run_more_spider('rack_hist')
            else:
                log.msg('Date of last invoice less than a month')
        else:
            log.msg("No hist invoice with date")

    def run_more_spider(self, name):
        url = 'http://localhost:6800/schedule.json'
        data = {
                'project': 'rack',
                'spider': name,
                'setting': 'USER_ID=%s' % self.user_id
                }
        req = urllib2.Request(url, urlencode(data))

        try:
            res = urllib2.urlopen(req)
        except Exception, e:
            log.msg("Cant start spider %s" % str(e))
        else:
            log.msg("Run spider %s  with response %s" % (name, str(res.read())))
        return

    def close_spider(self, spider):
        rusage = []
        rservers = []
        if spider.close_down or not self.account_id or not self.user_id:
            return
        if spider.name == 'rack_current':
            self.mongodb[RackServers._collection_name].remove(dict(
                cloud_account_id = self.user_id,
                account_id = unicode(self.account_id),
                invoice_id = u""
                ))
            log.msg("Total usage data %s" %
                    str(self.totalusage.get_mongo_obj()))
            if self.totalusage:
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




    def _write_to_mongo(self, bulk, col):
        if not bulk:
            return
        self.mongodb[col].insert(bulk)
        return

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

    def _get_credentials(self):
        user = self.session.query(Users).filter_by(id=self.user_id).first()
        if user:
            return (user.account_user, user.password, user.account_id != "")
        else:
            return (None, None, False)

    def _update_account_id(self):
        return
        if not self.user_id or not self.account_id:
            return
        user = self.session.query(Users).filter_by(id=self.user_id).first()
        if user:
            user.account_id = self.account_id
            user.date_modified = datetime.datetime.now()
        self.session.commit()


class UserStorage(Base):
    __tablename__ = "user_storage_providers"
    __table_args__ = {"autoload": True}


class UserCloud(Base):
    __tablename__ = "user_cloud_providers"
    __table_args__ = {"autoload": True}


class Users(Base):
    __tablename__ = "user_cloud_accounts"
    __table_args__ = {"autoload": True}

    def __repr__(self):
        return "User(id=%d, name=%s, pass=%s)" % (self.id, self.account_user, self.password)

# Base.metadata.create_all(engine)
