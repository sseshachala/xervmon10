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

connect_str = 'mysql+mysqldb://%s:%s@%s/%s' % (settings['MYSQL_USER'],
        settings['MYSQL_PASSWORD'], settings['MYSQL_HOST'], settings['MYSQL_DB'])
engine = create_engine(connect_str, echo=False)
Base = declarative_base()
SqliteSession = sessionmaker(bind=engine)
SESSION = SqliteSession()
Base.metadata.bind = engine

LOGCOL = settings.get("MONGO_LOG")

def mongo_connect():
    MONGO_CONN = pymongo.Connection(settings.get('MONGO_HOST'))
    MONGO_CONN = MONGO_CONN[settings['MONGO_DB']]
    MONGO_CONN.authenticate(settings['MONGO_USER'], settings['MONGO_PASSWORD'])
    return MONGO_CONN

MONGO_CONN = mongo_connect()

class StatusPipeline(object):
    def __init__(self):
        self.mongodb = MONGO_CONN
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
        self.mongodb = mongo_connect()
        cmd = spider.name
        e = ''
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
        if not user:
            msg += 'No user found with id %s' % (self.user_id)
        else:
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


class BaseMongoDBPipeline(object):
    def __init__(self):
        self.username = None
        self.passowrd = None
        self.provider_id = None
        self.got_acid = False
        self.session = SESSION
        self.mongodb = MONGO_CONN
        self.service_col = 'providers_services'
        self.user_id = settings.get('USER_ID')
        log.msg('User id is %s' % self.user_id)
        self.closeEngine = ''
        self.check_mongo_conn()
        if not self.user_id:
            self.closeEngine = 'No user id. '


    def check_mongo_conn(self):
        try:
            self.mongodb.collection_names()
        except Exception, e:
            self.closeEngine += 'Mongo connection error %s' % str(e)
            log.msg('%s %s' % (settings['MONGO_DB'], self.mongodb))
            raise

    def open_spider(self, spider):
        self._get_credentials()
        if self.closeEngine:
            log.msg(self.closeEngine)
            spider.close_down = True
            spider.errors.append(self.closeEngine)
            return False
        if not self.username or not self.password:
            log.msg('No login or password')
            spider.errors.append('No login or password')
            spider.close_down = True
            return False
        spider.new_services = []
        return True

    def close_spider(self, spider):
        if spider.close_down or not self.account_id or not self.user_id:
            return False
        self.mongodb = mongo_connect()
        if hasattr(spider, 'new_services') and spider.new_services:
            cur_services = [s['name'] for s in self.mongodb[self.service_col].find(dict(id=self.provider_id))]
            now = datetime.datetime.now()
            servic = [{'id': self.provider_id, 'name': s, 'date': now} for s in spider.new_services if not s in cur_services]
            self._write_to_mongo(servic, self.service_col)
        return True

    def ensure_index(self, Item):
        if not hasattr(Item, '_mongo_keys') or not hasattr(Item,
                '_collection_name'):
            return
        for i in Item._mongo_keys:
            self.mongodb[Item._collection_name].ensure_index(i)

    def run_more_spider(self, name):
        url = 'http://localhost:6800/schedule.json'
        setting = ('USER_ID', 'MONGO_DB', 'MYSQL_DB')
        data = {
                'project': settings.get('BOT_NAME'),
                'spider': name,
                }
        req = urllib2.Request(url, urlencode(data) + '&' + '&'.join(map(lambda s:urlencode({'setting': '%s=%s' % (s, settings.get(s))}), setting)))

        try:
            res = urllib2.urlopen(req)
        except Exception, e:
            log.msg("Cant start spider %s" % str(e))
        else:
            log.msg("Run spider %s  with response %s" % (name, str(res.read())))
        return

    def _write_to_mongo(self, bulk, col):
        if not bulk:
            return
        mongo_insert = 1000
        for b in xrange(0, len(bulk), mongo_insert):
            self.mongodb[col].insert(bulk[b:b + mongo_insert])
        return

    def _get_credentials(self):
        try:
            user = self.session.query(Users).filter_by(id=self.user_id).first()
        except Exception, e:
            self.closeEngine += ("Couldn`t get mysql user. %s" % str(e))
            return None
        if user:
            self.account_id = user.account_id
            self.provider_id = user.cloud_provider
            try:
                self.password = self._decrypt_password(user.password)
            except Exception, e:
                self.closeEngine += ("Couldn`t decrypt password. %s" % str(e))
            self.username = user.account_user
            if self.account_id != "":
                self.got_acid = True

            return user
        else:
            return None

    def _decrypt_password(self, password):
        key = settings.get('KEY')
        if not key:
            return password
        import rijndael
        import base64
        dcode = base64.b64decode(password)
        key_size = 16
        block_size = 32
        key = key.ljust(key_size, '\0')
        enc = rijndael.rijndael(key, block_size)
        padded_text = ''
        # tweak from padded text from php encryption
        # http://stackoverflow.com/questions/8217269/decrypting-strings-in-python-that-were-encrypted-with-mcrypt-rijndael-256-in-php
        for start in range(0, len(dcode), block_size):
            padded_text += enc.decrypt(dcode[start:start+block_size])
        password = padded_text.split('\x00', 1)[0]
        return password


    def _update_account_id(self):
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
