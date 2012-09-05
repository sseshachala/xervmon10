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
        datesel = soup.find('select',
                id=re.compile('ReportViewer2(.*)ddValue'))
        select_id = datesel.get('name')
        dates = datesel.findAll('option')
        self.log.msg('Select id is %s' % select_id)
        form = soup.find('form', id='form1')
        inps = form.findAll('input')
        formdata = {}
        for inp in inps:
            inp_name = inp.get('name')
            if not inp_name:
                continue
            formdata[inp_name] = inp.get('value', '')
        self.allrequest = []
        for dat in dates:
            formdata_it = formdata.copy()
            try:
                datmonth = datetime.datetime.strptime(dat.text, '%b-%Y')
            except:
                continue
            if '%s-%s' % (datmonth.month, datmonth.year) in self.invoices:
                self.log.msg("Invoice %s already in db. Skipping" % datmonth)
                continue
            datval = dat.get('value')
            self.log.msg("Found invoice date %s with value %s" % (datmonth,
                dat.get('value')))
            formdata_it[select_id] = datval
            rargs = [response.url]
            rkwargs = dict(
                    formdata=formdata_it, callback=self.get_csv, meta={'month':
                        datmonth}, dont_filter=True, headers={'referer': response.url})
            self.allrequest.append({'a': rargs, 'k': rkwargs})
        yield self.update_month()

    def get_csv(self, response):
        body = response.body
        meta = response.request.meta
        try:
            url_base = re.findall('"([^"]+OpType=Export[^"]+)"',
                    body)[0].replace('\\', '')
        except:
            self.log.msg("Error finding csv url")
            return
        return Request(urlparse.urljoin(self._DOWNLOAD_URL, url_base+"CSV"),
                callback=self.parse_csv, meta=meta, dont_filter=True, priority=5)


    def parse_csv(self, response):
        meta = response.request.meta
        self.log.msg("get csv file month %s" % meta['month'])

        import csv
        from io import BytesIO
        csv_body = response.body
        csv_body = csv_body.replace('\0', '')
        o = BytesIO(csv_body)
        reader = csv.reader(o)
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
        item_services = {}
        for e in entries:
            cat_name = e['RECTYPELETTERCODE'].split(':')
            if len(cat_name) > 1:
                cat_name = ':'.join(cat_name[1:]).strip()
            else:
                cat_name = cat_name[0]
            cat_name = cat_name.strip()
            if not cat_name in services:
                services[cat_name] = {}
            cat = services[cat_name]
            if not 'total' in cat:
                cat['total'] = e['BILLABLE_AMOUNT1']

            subcat_name = e['GENERAL_CHARGES_CATEGORY_DESC'].strip()
            if not subcat_name in cat:
                cat[subcat_name] = {}
            subcat = cat[subcat_name]
            charge = round(float(e['SUMOFBILLABLE_AMOUNT'].replace('$', '').replace(',', '')), 2)
            service_name = '%s-%s-%s' % (cat_name, subcat_name, e['CHARGED_DESC'])
            if subcat == 'TAXES AND SURCHARGES':
                if not 'taxes' in item_services:
                    item_services['taxes'] = 0
                item_services['taxes'] += charge
            else:
                if not service_name in item_services:
                    item_services[service_name] = 0
                item_services[service_name] += charge

            continue
            # we dont need it now

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
        inv['services'] = item_services
        yield inv
        yield self.update_month()

    def update_month(self):
        try:
            req = self.allrequest.pop()
        except:
            return
        rargs = req['a']
        rkwargs = req['k']
        return FormRequest(*rargs, **rkwargs)





