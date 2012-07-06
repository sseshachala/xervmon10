#!/usr/bin/env python 

import re
import datetime
import urlparse
from dateutil.relativedelta import relativedelta
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider

from BeautifulSoup import BeautifulSoup

from timewarner.items import *

from timewarner_base import TimewarnerSpiderBase

class TimewarnerHistorySpider(TimewarnerSpiderBase):
    name = 'timewarner_history'

    def parse_timewarner(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        iframe = soup.find('iframe',
                id='ctl00_MasterMainContentPlaceHolder_ifReports')
        src = iframe.get('src')
        if not src:
            self.log.msg("Cant find iframe %s" % str(iframe))
            yield
        yield Request(src, headers={'Referer': self._BILLS_URL}, callback=self.parse_iframe)

    def parse_iframe(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        accounts = soup.find('select', id="ddAccountList")
        curaccount = accounts.find('option', selected='selected')
        acc = TimewarnerAccount()
        acc['account_id'] = curaccount.text
        yield acc
        self.log.msg("Cur account %s" % curaccount.text)
        dates = soup.find('select',
                id='ReportViewer2_ctl00_ctl03_ddValue').findAll('option')
        form = soup.find('form', id='form1')
        inps = form.findAll('input')
        formdata = {}
        for inp in inps:
            inp_name = inp.get('name')
            if not inp_name:
                continue
            formdata[inp_name] = inp.get('value', '')
        for dat in dates:
            try:
                datmonth = datetime.datetime.strptime(dat.text, '%b-%Y')
            except:
                continue
            datval = dat.get('value')
            self.log.msg("Found invoice date %s with value %s" % (datmonth,
                dat.get('value')))
            formdata["ReportViewer2$ctl00$ctl03$ddValue"] = datval
            yield FormRequest(response.url,
                    formdata=formdata, callback=self.get_csv, meta={'month':
                        datmonth})


    def get_csv(self, response):
        body = response.body
        meta = response.request.meta
        try:
            url_base = re.findall('"([^"]+OpType=Export[^"]+)"',
                    body)[0].replace('\\', '')
        except:
            self.log.msg("Error finding csv url")
            yield
        self.log.msg("Parse url %s" % url_base)
        yield Request(urlparse.urljoin(self._DOWNLOAD_URL, url_base+"CSV"),
                callback=self.parse_csv, meta=meta, dont_filter=True)


    def parse_csv(self, response):
        meta = response.request.meta
        self.log.msg("get csv file month %s" % meta['month'])

        import csv
        csv_body = response.body
        reader = csv.reader(csv_body.split('\r\n'))
        lines = [l for l in reader]
        names = [l.strip() for l in lines[0]]
        if len(lines) < 2:
            yield
        entries = []
        for l in lines[1:]:
            if not l:
                continue
            entries.append(dict(map(lambda x,y: (x, y.strip()), names, l)))
        def parse_csv_date(date):
            date_format = '%m/%d/%Y'
            try:
                edate = datetime.datetime.strptime(date,
                        date_format)
            except:
                edate = None
            return edate
        inv = TimewarnerData()
        inv['total'] = entries[0]['SUM_BILLABLE_AMOUNT']
        inv['enddate'] = parse_csv_date(entries[0]['BILLING_DATE'])
        inv['startdate'] = None
        if inv['enddate']:
            inv['startdate'] = inv['enddate'] +relativedelta(months=-1, days=+1)

        services = {}
        for e in entries:
            cat = e['RECTYPELETTERCODE'].split(':')
            if len(cat) > 1:
                cat = ':'.join(cat[1:])
            else:
                cat = cat[0]
            cat = cat.strip()
            if not cat in services:
                services[cat] = {}
            cat = services[cat]
            if not 'total' in cat:
                cat['total'] = e['BILLABLE_AMOUNT1']

            subcat = e['GENERAL_CHARGES_CATEGORY_DESC']
            if not subcat in cat:
                cat[subcat] = {}
            subcat = cat[subcat]
            if not 'total' in subcat:
                subcat['total'] = e['BILLABLE_AMOUNT']

            try:
                startdate, enddate = e['CHARGE_TO_DATE'].split('-')
            except:
                startdate = enddate = None
            startdate = parse_csv_date(startdate)
            enddate = parse_csv_date(enddate)

            item = {}
            item['name'] = e['CHARGED_DESC']
            item['quan'] = e['SUMOFITEM_QUANTITY']
            item['startdate'] = startdate
            item['enddate'] = enddate
            subcat[item['name']] = item
        inv['services'] = services
        yield inv





