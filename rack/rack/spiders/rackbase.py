import re
import demjson
import datetime
import time
from BeautifulSoup import BeautifulSoup

from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider

from rack.items import *


class RackSpiderBase(BaseSpider):
    _urls = settings.get('URLS')
    if isinstance(_urls, dict):
        vars().update(_urls)
    start_urls = [_URL_LOGIN]


    def __init__(self, *args, **kwargs):
        super(RackSpiderBase, self).__init__(*args, **kwargs)
        self.account_id = None
        self.username = None
        self.password = None
        self.close_down = False
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

        return [FormRequest.from_response(response, formname="LoginForm",
            formdata={"username": self.username, "password": self.password},
            callback=self.after_login)]

    def after_login(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        error = soup.find("div", "fieldError")
        if error:
            self.log.msg(error)
            self.close_down = True
            raise CloseSpider("bad login")
            yield

        loginfo = soup.find("div", "logged-in-as")
        if not loginfo:
            yield
        loginfo_txt = "".join(loginfo.findAll(text=True)).strip()
        m = re.search("#([0-9]{4,})", loginfo_txt)
        if m and len(m.groups()):
            acc = RackAccount()
            acc['account_id'] = m.group(1)
            yield acc
        yield Request(self._URL_BILLING, dont_filter=True, callback=self.parse_rack)

    def parse_rack(self, response):
        "To implement"
        raise NotImplementedError("You have to reimplement this method in derived class")

    def _parse_invoice(self, data):
        startinv = endinv = None
        items = []
        soup = BeautifulSoup(re.sub('<!DOCTYPE(.*)>', '', data))

        invoice = soup.find('table', 'invoice')
        if not invoice:
            raise
        period = invoice.find(text=lambda x:"Coverage Period" in x)
        if period:
            startt = " ".join(period.split()[:-4])
            endt = " ".join(period.split()[-3:])
            startinv = datetime.datetime.strptime(startt,
                    "Coverage period: %b %d, %Y")
            endinv = datetime.datetime.strptime(endt,
                    "%b %d, %Y")
        try:
            invoice_id = invoice.find("div", "invoice-id").text
        except AttributeError:
            invoice_id = ''
        try:
            invoice_amount = invoice.find("span", "amount-due").text
        except AttributeError:
            invoice_amount = ''

        rackinv = RackServers()
        rackinv['invoice_id'] = invoice_id
        rackinv['amount'] = invoice_amount
        rackinv['startdate'] = startinv
        rackinv['enddate'] = endinv

        rows = invoice.findAll('tr', 'itemRow')
        for row in rows:
            item = RackUsage()
            item['usagetype'] = row.td.strong.text
            dest = row.td.ul.li.text
            if dest:
                if 'Server name' in dest:
                    split = dest.split('Server name:')
                    item['server'] = split[-1].strip()
                    usage = re.search("([0-9.]+)", split[0])
                else:
                    item['server'] = ''
                    usage = re.search("([0-9.]+)", dest)
                if usage and len(usage.groups()):
                    item['usagevalue'] = usage.group(1)
                else:
                    item['usagevalue'] = ''
                try:
                    service = row.td.nextSibling.nextSibling.text.split("-")
                    item['service'] = service[0].strip()
                    item['operation'] = service[1].strip()
                except:
                    item['service'] = item['operation'] = ''
                item['cost'] = ''
                try:
                    item['cost'] = row.findAll('td', 'even')[2].strong.text
                except:
                    pass

                item['startdate'] = startinv
                item['enddate'] = endinv
                item['invoice_id'] = invoice_id
                yield item

    def _parse_js_table(self, data):
        "Return python dict"
        jsdic = None
        st = data.find('{')
        en = data.rfind('}')
        if not st or not en:
            return jsdic
        try:
            jsdic = demjson.decode(data[st:en+1])
        except:
            return

        def parse_val(jd):
            for k, v in jd.items():
                if v and isinstance(v, basestring) and v[0] in ('[', '{'):
                    try:
                        parsed = demjson.decode(v)
                    except:
                        continue
                    parsed_all = parse_val(parsed)
                    jd[k] = parsed_all
            return jd

        jsdic = parse_val(jsdic)
        names = [c['mappingName'] for c in jsdic['tableDefinition0']['columns']]
        items = [dict(zip(names, r)) for r in jsdic['tableData0']['rows']]
        return items


