#!/usr/bin/env python

import pymongo
import csv
import datetime
import StringIO
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scrapy.conf import settings
from scrapy import log
from amazon.items import AmazonCharges, AmazonAccount, AmazonUsage

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
#        self.email(status, cmd, e)
        self.log(status, cmd, e)

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
        self.service_map = settings['SERVICE_MAP']
        self.amazon_prices = []
        self.user_id = settings.get('USER_ID')
        log.msg('User id is %s' % self.user_id)
        self.acharges = []
        self.ausage = []
        self.account_id = None
        self.old_usage = []
        self.old_charges = []
        self.iam = False
        self.session = SESSION

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
        fields = ['cloud_account_id', 'service', 'startdate', 'enddate']
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


    def _write_to_mongo(self, bulk, col):
        if not bulk:
            return
        self.mongodb[col].insert(bulk)


    def _get_credentials(self):
        user = self.session.query(Users).filter_by(id=self.user_id).first()
        if not user:
            return (None, None, False)
        cred_type = user.credentail_type
        self.account_id = user.account_id
        if cred_type == 'IAM':
            self.iam = True
        else:
            self.iam = False
        return (user.account_user, user.password, user.account_id != "")

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
