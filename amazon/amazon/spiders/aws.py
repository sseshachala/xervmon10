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
    IAM_LOGIN_URL = 'https://%s.signin.aws.amazon.com/console'
    _ACCOUNT_SUMMARY_URL = "https://aws-portal.amazon.com/gp/aws/developer/account/index.html?ie=UTF8&action=activity-summary"
    start_urls = [_ACCOUNT_SUMMARY_URL]

    def __init__(self, *args, **kwargs):
        super(AwsSpiderBase, self).__init__(*args, **kwargs)
        self.account_id = None
        self.invoices = []
        self.close_down = False
        self.username = None
        self.password = None
        self.errors = []
        self.log = log

    def parse(self, response):
        if self.close_down:
            raise CloseSpider('No user id')
            return
        if not self.username or not self.password:
            self.close_down = True
            self.log.msg("No credentials", level=log.ERROR)
            raise CloseSpider('No credentials')
            return
        resp = response.replace(body=re.sub('<!DOCTYPE(.*)>', '', response.body))
        return [FormRequest.from_response(resp, formname='signIn',
            formdata={
                'email':self.username,
                'password': self.password
                },
            callback=self.after_login)]

    def after_login(self, response):
        soup = BeautifulSoup(response.body)
        error = soup.find("div", id="message_error")
        self.log.msg("Go to parsing")
        if error:
            self.log.msg("Error login")
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
            raise CloseSpider("bad login")
            yield
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
        if 'date_from' not in meta or 'date_to' not in meta:
            return
        date_from = meta['date_from']
        date_to = meta['date_to']
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
            callback=self._parse_csv)


    def _parse_date(self, datestr):
        try:
            datestr = datetime.datetime.strptime(datestr, "%m/%d/%y %H:%M:%S")
        except:
            datestr = None
        return datestr

    def _parse_csv(self, response):
        csvdata = response.body
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
            item = AmazonUsage()
            item['service'] = row[0]
            item['operation'] = row[1]
            item['usagetype'] = row[2]
            item['starttime'] = self._parse_date(row[3])
            item['endtime'] = self._parse_date(row[4])
            item['usagevalue'] = row[5]
            yield item
