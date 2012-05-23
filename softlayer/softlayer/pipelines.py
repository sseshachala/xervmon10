#!/usr/bin/env python

import pymongo
import csv
import datetime
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
from softlayer.items import *

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
    CURRENT_INVOICE = u'0000000000'

    def __init__(self):
        log.msg(settings.get('MONGO_HOST'))
        self.mongodb = MONGO_CONN[settings['MONGO_DB']]
        self.user_id = settings.get('USER_ID')
        log.msg('User id is %s' % self.user_id)
        self.sinvoices = []
        self.susage = []
        # List of servers with info 
        self.account_id = None
        self.got_acid = False
        # From mongodb
        self.old_usage = []
        self.old_invoices = []
        # sqlalchemy session
        self.session = SESSION

    def process_item(self, item, spider):
        if not self.account_id and isinstance(item, SoftlayerAccount):
            self.account_id = item['account_id']
            self._update_account_id()
        elif isinstance(item, SoftlayerInvoice):
            item['cloud_account_id'] = self.user_id
            obj = item.get_mongo_obj()
            self.sinvoices.append(obj)
        elif isinstance(item, SoftlayerUsage):
            item['cloud_account_id'] = self.user_id
            obj = item.get_mongo_obj()
            self.susage.append(obj)
        return item

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

    def run_more_spider(self, name):
        url = 'http://localhost:6800/schedule.json'
        data = {
                'project': 'softlayer',
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
        if spider.close_down or not self.account_id or not self.user_id:
            return
        if spider.name == 'softlayer_current':
            self.mongodb[SoftlayerUsage._collection_name].remove(dict(cloud_account_id=self.user_id,
                invoice_id=self.CURRENT_INVOICE))
            self.mongodb[SoftlayerInvoice._collection_name].remove(dict(cloud_account_id=self.user_id,
                invoice_id=self.CURRENT_INVOICE))
        self._write_to_mongo(self.sinvoices, SoftlayerInvoice._collection_name)
        self._write_to_mongo(self.susage, SoftlayerUsage._collection_name)

    def _write_to_mongo(self, bulk, col):
        if not bulk:
            return
        self.mongodb[col].insert(bulk)
        return

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



class Users(Base):
    __tablename__ = "user_cloud_accounts"
    __table_args__ = {"autoload": True}

    def __repr__(self):
        return "User(id=%d, name=%s, pass=%s)" % (self.id, self.account_user, self.password)

Base.metadata.create_all(engine)
