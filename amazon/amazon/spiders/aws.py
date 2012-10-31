#!/usr/bin/env python
import re
import csv
import datetime
import time
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.conf import settings
from scrapy.exceptions import CloseSpider

from BeautifulSoup import BeautifulSoup

from amazon.items import *

class AwsSpiderBase(BaseSpider):
    _urls = settings.get('URLS')
    if isinstance(_urls, dict):
        vars().update(_urls)
    start_urls = []

    def __init__(self, *args, **kwargs):
        super(AwsSpiderBase, self).__init__(*args, **kwargs)
        self.account_id = None
        self.invoices = []
        self.close_down = False
        self.iam = False
        self.username = None
        self.password = None
        self.errors = []

    def start_requests(self):
        if self.iam:
            url = self.IAM_LOGIN_URL % self.account_id
            self.log("IAM mode with starturl %s" % str(url))
        else:
            url = self._ACCOUNT_SUMMARY_URL
        yield Request(url, callback=self.parse)


    def parse(self, response):
        if self.close_down:
            self.errors.append("Bad credentials")
            raise CloseSpider('Bad credentials')
            return
        resp = response.replace(body=re.sub('<!DOCTYPE(.*)>', '', response.body))
        return [FormRequest.from_response(resp, formname='signIn',
            dont_filter=True,
            formdata={
                'email':self.username,
                'password': self.password
                },
            callback=self.after_login)]

    def after_login(self, response):
        content = re.sub('<!DOCTYPE(.*)>', '', response.body)
        soup = BeautifulSoup(content)
        error = soup.find("div", id="message_error")
        if error:
            err = ('Error login %s' % error.text)
            self.log(err)
            self.errors.append(err)
            self.close_down = True
            raise CloseSpider("bad login")
            yield
        acid = soup.find("span", attrs={"class": "txtxxsm"})
        m = None
        if acid:
            acid_txt = "".join(acid.findAll(text=True)).strip()
            m = re.search("Account Number ([0-9]{4}-[0-9]{4}-[0-9]{4})", acid_txt)
        if m and len(m.groups()):
            account = AmazonAccount()
            account['account_id'] = m.group(1)
            yield account
        elif self.iam:
            pass
        else:
            self.close_down = True
            self.errors.append('Login error getting account_id')
            raise CloseSpider("bad login")
            yield
        self.log("Go to parsing")
        yield Request(self._ACCOUNT_SUMMARY_URL, dont_filter=True, callback=self.parse_aws)

    def parse_aws(self, response):
        """interface method for spider logic"""
        raise NotImplementedError("This method have to be overriden in derived class")


    def _parse_charges(self, data):
        "Parse charges for cur data"

        ret = []
        soup = BeautifulSoup(data)
        billing = soup.find("div", id="account_activity_table_tab_content")
        if not billing:
            return ret
        services = billing.findAll("span", attrs={"class":"hdrdkorange"})
        for f in services:
            service = "".join(f.findAll(text=True))
            anchor = f.parent.find("a")
            if anchor:
                link = anchor.attrs[0][1]
            else:
                link = None
            cost = "".join(f.parent.findNextSibling("td").findAll(text=True)).strip()
            charge = AmazonCharges()
            charge['link'] = link
            charge['cost'] = float(cost.replace("&#36;", ""))
            charge['service'] = service
            ret.append(charge)
        return ret

    def get_report(self, response):
        meta = response.request.meta
        item = meta['item']
        if 'startdate' not in item or 'enddate' not in item:
            return
        date_from = item['startdate']
        date_to = item['enddate']
        form_data = {
                'timePeriod': 'aws-portal-custom-date-range',
                'startYear': str(date_from.year),
                'startMonth': str(date_from.month),
                'startDay': str(date_from.day),
                'endYear': str(date_to.year),
                'endMonth': str(date_to.month),
                'endDay': str(date_to.day),
                'periodType': 'hours',
                'download-usage-report-csv': '1'
            }
        yield FormRequest.from_response(response,
            formname='usageReportForm', formdata=form_data,
            meta=meta,
            callback=self._parse_csv)


    def _parse_date(self, datestr):
        try:
            datestr = datetime.datetime.strptime(datestr, "%m/%d/%y %H:%M:%S")
        except:
            datestr = None
        return datestr

    def check_permission(self, response):
        if response.url == 'https://portal.aws.amazon.com/gp/aws/401.html':
            self.errors.append('Permission denied')
            return False
        return True

    def _parse_csv(self, response):
        csvdata = response.body
        meta = response.request.meta
        service_item = meta['item']
        fp = StringIO(csvdata)
        c = csv.reader(fp)
        header = c.next()
        old_format = len(header) == 7
        docs = []
        for row in c:
            if not row:
                continue
            if len(row):
                if old_format:
                    # Before Jan 2011, downloaded files had 7
                    # columns, not 6.
                    row = row[:3] + row[4:]
            item = {}
            item['operation'] = row[1]
            item['usagetype'] = row[2]
            item['starttime'] = self._parse_date(row[3])
            item['endtime'] = self._parse_date(row[4])
            item['usagevalue'] = row[5]
            service_item['usage'].append(item)
        yield service_item
