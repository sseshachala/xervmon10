#!/usr/bin/env python

import sys
import os
import datetime
import time
import re
import csv
import traceback

import sqlalchemy
import pymongo

from selenium import webdriver

import conf

HOST = 'mongodb://%s:%s@%s:%s/%s' % (conf.mongo_user, conf.mongo_password, conf.mongo_host, conf.mongo_port, conf.mongo_dbname)
conn = pymongo.Connection(HOST)
db = conn[conf.mongo_dbname]
LOGCOL = 'scrape_log'


def get_login(user_id):
    user = conf.session.query(Users).filter_by(id=user_id).first()
    if user:
        return (user.account_user, user.password, user.account_id != "")
    else:
        return (None, None, False)

def update_account_id(user_id, account_id):
    user = conf.session.query(Users).filter_by(id=user_id).first()
    if user:
        user.account_id = account_id
        user.date_modified = datetime.datetime.now()
    conf.session.commit()


def load_current_data(user_id):
    "Load last invoice and current usage and update db"
    print "Updating current data"
    # u, p, got_acid = get_login(user_id)
    u,p = 'info@tabillo.com','qimsdev-2010'
    login_url = 'https://login.live.com'
    billing_url = 'https://account.windowsazure.com/Subscriptions'
    download_dir = '/home/sysadmin/Downloads'
    if u is None and p is None:
        print >>sys.stderr, "No login details for cloud_accounts id", user_id
        return
    user_folder = ''
    browser = webdriver.Chrome()
    f = browser
    f.get(login_url)
    f.find_element_by_name('login').send_keys(u)
    f.find_element_by_name('passwd').send_keys(p)
    f.find_element_by_name('passwd').submit()
    f.get(billing_url)
    time.sleep(3)
    try:
        f.find_element_by_class_name('subscription-item').click()
    except:
        f.find_element_by_name('passwd').send_keys(p)
        f.find_element_by_name('passwd').submit()
	time.sleep(3)
        f.find_element_by_class_name('subscription-item').click()
    finally:
        f.get_screenshot_as_file('/home/sysadmin/%s' % '1.png')

    idnum = f.find_element_by_id('subscription-friendly-id').text
    for fil in os.listdir(download_dir):
        if idnum in fil:
            os.remove(os.path.join(download_dir, fil))

    f.find_element_by_class_name('download').click()
    time.sleep(3)
    f.close()

    path = os.path.join(download_dir, '%s.csv' % idnum)
    items = parse_csv(path)
    try:
        recent_item = db['azure_usage'].find().sort("Timestamp", pymongo.DESCENDING).limit(1).next()
        recent_date = recent_item['Timestamp']
    except StopIteration:
        recent_date = datetime.datetime.now()
    current_items_curs = db['azure_usage'].find({"Timestamp": {"$gte": recent_date}})
    db_items = [c['ResourceGuid'] for c in current_items_curs]
    to_db = []
    for item in items:
        if item['ResourceGuid'] in db_items:
            continue
        item['Timestamp'] = datetime.datetime.strptime(item['Timestamp'], '%m/%d/%Y')
        item['cloud_account_id'] = user_id
        to_db.append(item)

    if to_db:
        db['azure_usage'].insert(to_db)

    return items


def parse_csv(filename):
    with open(filename) as fp:
        csvread = csv.reader(fp.readlines())
    names = csvread.next()
    for i, n in enumerate(names):
        names[i] = n.decode('utf-8-sig')
    items = [dict(zip(names, it)) for it in csvread]
    return items


def update_usage():
    pass

def log(uid, status, error=''):
    now = datetime.datetime.now()
    prevday = now - datetime.timedelta(days=1)
    db[LOGCOL].remove({"user_id": uid, "added": { "$gt": prevday}})
    db[LOGCOL].insert({"user_id": uid, "status": status, "traceback": error,
        "script": "azure", "added": now})


class Users(conf.Base):
    __tablename__ = "user_cloud_accounts"
    __table_args__ = {"autoload": True}

    def __repr__(self):
        return "User(id=%d, name=%s, pass=%s)" % (self.id, self.account_user, self.password)

conf.Base.metadata.create_all(conf.engine)



if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        uid = sys.argv[1]
        log(uid, 'Working')
        try:
            load_current_data(uid)
        except:
            e = traceback.format_exc()
            print str(e)
            log(uid, 'Error', e)
            browser.close()
        else:
            log(uid, 'Success')

    else:
        print >>sys.stderr, "Usage: %s user_id [all]" % sys.argv[0]
