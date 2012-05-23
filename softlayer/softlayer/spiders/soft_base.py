#!/usr/bin/env python
import re
import datetime
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider

from BeautifulSoup import BeautifulSoup
import xlrd

from softlayer.items import *

class SoftlayerSpiderBase(BaseSpider):
    _BILLING_URL = "https://manage.softlayer.com/Administrative/accountSummary"
    start_urls = [_BILLING_URL]

    def __init__(self, *args, **kwargs):
        super(SoftlayerSpiderBase, self).__init__(*args, **kwargs)
        self.account_id = None
        self.invoices = []
        self.close_down = False
        self.username = None
        self.password = None
        self.username = 'ssudhendra'
        self.password = '!Pipeline1'
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
        return [FormRequest.from_response(resp, formname='loginform',
            formdata={
                'data[User][username]':self.username,
                'data[User][password]': self.password
                },
            callback=self.after_login)]

    def after_login(self, response):
        soup = BeautifulSoup(response.body)
        error = soup.find("span", "error_message")
        if error:
            self.log.msg("Error login")
            self.close_down = True
            raise CloseSpider("bad login")
            yield
        self.log.msg("Go to parsing")
        acid = soup.find("div", id="userinfo")
        if not acid:
            self.close_down = True
            raise CloseSpider("bad login")
            yield
        yield Request(self._BILLING_URL, dont_filter=True,
                callback=self.parse_softlayer)

    def parse_softlayer(self, response):
        """interface method for spider logic"""
        raise NotImplementedError("This method have to be overriden in derived class")

    def _parse_invoice(self, data):
        "Parse xls invoice file"
        now = datetime.datetime.now()
        contents = data.body
        workbook = xlrd.open_workbook(file_contents=contents)
        detail_sheet = u'Detailed Billing'
        summary_sheet = u'Summary'
        if not all(map(lambda sh: sh in workbook.sheet_names(),
            [detail_sheet, summary_sheet])):
            return
        summary = workbook.sheet_by_name(summary_sheet)
        scells = []
        for n in xrange(summary.nrows):
            scells.append(summary.row_values(n))

        try:
            idcell = summary.cell_value(11, 1)
            invoice_id = idcell.split()[-1]
        except IndexError:
            return

        if not self.account_id:
            try:
                acell = summary.cell_value(12, 1)
                self.account_id = acell.split()[-1]
                it = SoftlayerAccount()
                it['account_id'] = self.account_id
                yield it
            except:
                pass

        invoice_date_t = summary.cell_value(1, 9)
        try:
            invoice_date = datetime.datetime.strptime(
                    invoice_date_t, '%d %b %Y')
        except Exception, e:
            self.log.msg(str(e))
            invoice_date = None

        invoice = SoftlayerInvoice()
        invoice['invoice_id'] = invoice_id
        invoice['enddate'] = ''
        if isinstance(invoice_date, type(now)):
            invoice['enddate'] = invoice_date

        details = workbook.sheet_by_name(detail_sheet)
        usage = []
        usage_entry = []
        for row in xrange(1, details.nrows):
            # list start with 0 it is easier to handle as in excel file
            cell = lambda col: details.cell_value(row, col - 1)
            if cell(2) == u'Total:':
                invoice_total = cell(9)
                break
            if not cell(2):
                if usage_entry:
                    usage.append(usage_entry)
                    usage_entry = []
                continue
            usage_entry.append(details.row_values(row))

        invoice['cost'] = invoice_total
        yield invoice

        def parse_row(row):
            spec = {}
            if len(row) != 12:
                self.log.msg("Bad format of excel")
                return spec
            name = row[1]
            spl = name.split(':')
            spec['category'] = spl[0]
            spec['name'] = ':'.join(spl[1:])
            spec['cost'] = row[8]
            spec['location'] = row[7]
            return spec

        for u in usage:
            item = SoftlayerUsage()
            item['enddate'] = invoice['enddate']
            item['invoice_id'] = invoice['invoice_id']
            subtotal = u.pop()
            item['cost'] = subtotal[8]
            if len(u) == 1:
                item['name'] = ''
                item['spec'] = [parse_row(u[0])]
                yield item
                continue
            item['name'] = u[0][1]
            item['spec'] = map(parse_row, u[1:])
            yield item



