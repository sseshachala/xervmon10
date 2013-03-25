# -*- coding: utf-8 -*-#
#from __future__ import absolute_import

import urlparse
import datetime
import pprint

from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule

from scrapy.http import FormRequest, Request
# from scrapy.utils.response import open_in_browser
from scrapy import log
from scrapy.exceptions import CloseSpider

# import sys
# print "sys.path=",sys.path

from hpcloud2.items import Hpcloud2Item, HPCloudCurrent, HPCloudData


def get_all_text(t):
    tl = t.select('.//text()').extract()
    if isinstance(tl, list):
        return "".join(tl).strip()
    return tl

def clean_num(val):
    res = 0
    if isinstance(val, (int, long, float)):
        return float(val)
    elif isinstance(val, basestring) and not val.strip():
        return 0

    try:
        raw_re = re.search('[0-9]+([,.][0-9]+)?', val).group()
        res = float(raw_re.replace(',', '.'))
    except Exception, e:
        res = 0
    return res

def razb_totals(te):
    colnames = dict({0: "name", 1: "cost"})
    result = []
    tl = te.select('.//tr')
    for t in tl:
        tdl = t.select('.//td')

        line = {}
        for k, td in enumerate(tdl):
            text = get_all_text(td).encode('utf-8')
            line[colnames[k]] = text
        result.append(line)
    return result


def razb_table(te):
    colnames = dict({0: "service", 1: "quantity", 2: "amount"})
    result = []
    tl = te.select('.//tr')
    for t in tl:
        tdl = t.select('.//td')
        line = {}
        if len(tdl) == 1:
            text = get_all_text(tdl[0]).encode('utf-8')
            line['subhead'] = text
        elif len(tdl) == 3:
            for k, td in enumerate(tdl):
                text = get_all_text(td).encode('utf-8').replace("\n", " ")
                line[colnames[k]] = text
        else:
            #print "unknown len",len(tdl)
            continue
        result.append(line)
    return result


class Hpcloud2Spider(CrawlSpider):
    name = 'hpcloud2'
    start_urls = ['https://console.hpcloud.com/login']
    invoice_url = "https://account.hpcloud.com/invoices"

    def __init__(self, *args, **kwargs):
        super(Hpcloud2Spider, self).__init__(*args, **kwargs)
        self.username = None
        self.password = None
        self.billno = 1
        self.close_down = False
        self.errors = []
        self.invoices = []
        self.log = log
        log.msg("hpcloud2 started")

    def parse(self, response):
        hxs = HtmlXPathSelector(response)
        auth_token = hxs.select('//input[@name="authenticity_token"]/@value').extract()
        if auth_token:
            #print "make login request",self.username,self.password
            return [FormRequest.from_response(response, formnumber=0,
                        formdata={"user[username]": self.username, "user[password]": self.password,
                            "authenticity_token":auth_token, "utf8":u"✓"
                            },
                        callback=self.after_login)]

    def after_login(self, response):
        hxs = HtmlXPathSelector(response)
        alert = hxs.select('//ul[@class="message-alert"]').extract()
        if alert:
            print "Invalid login"
            raise CloseSpider(alert)
            return
        yield Request(url=self.invoice_url, callback=self.parse_invoices)

    def parse_invoices(self, response):
        hxs = HtmlXPathSelector(response)
        years = hxs.select(
                '//select[@id="billing_year"]/option/@value').extract()
        for year in years:
            yield Request(url=('%s?year=%s' % (self.invoice_url, year)),
                    callback=self.parse_bills_list)

    def parse_bills_list(self, response):
        hxs = HtmlXPathSelector(response)
        allrefs = hxs.select('//td[@class="shrink"]/a')

        # allrefs = allrefs[:1]       # ONE OBJECT FOR DEBUG
        # print "ONE OBJECT PROCESSING!"

        for refs in allrefs:
            href = refs.select('@href').extract()[0]
            yield Request(url=urlparse.urljoin(response.url, href), callback=self.parse_bill)

    def parse_bill(self, response):
        inv = HPCloudData()
        # with open("bill%02d.html" % (self.billno,), "w") as f:
        #     f.write("".join(response.body))
        # self.billno += 1

        hxs = HtmlXPathSelector(response)
        elist = hxs.select('//section[@class="container-fluid"]/div[3]/section[1]/div/p[2]')
        el = elist[0]
        slist = el.select('.//strong/text()')
        templ = '%B %d, %Y'
        startdate = slist[0]
        inv['startdate'] = datetime.datetime.strptime(startdate.extract(), templ)
        enddate = slist[1]
        inv['enddate'] = datetime.datetime.strptime(enddate.extract(), templ)
        inv['invoice_number'] = slist[2].extract()
        if inv['invoice_number'] in self.invoices:
            log.msg("Skipping. Invoice number " + inv['invoice_number'] + " already in db")
            return
        self.invoices.append(inv['invoice_number'])
        tlist = hxs.select('//table[@class="table-info"]')
        services = {}
        for te in tlist:
            h3l = te.select('.//preceding-sibling::h3')
            if h3l:
                h3e = h3l[-1]
                h3text = h3e.select('text()')[0]
            h2l = te.select('.//preceding-sibling::h2')
            if h2l:
                h2e = h2l[-1]
                h2text = h2e.select('text()')[0]
            if h2l and h3l:
                key = h2text.extract().lower()
                if key == "compute - windows":
                    key = "compute_windows"

                tabledata = razb_table(te)
                services[key] = tabledata

        tlist = hxs.select('//section[@id="invoice_totals"]/table[@class="table-info"]')
        if tlist:
            table = razb_totals(tlist[0])
            inv['totals'] = table
            total = 0
            for tot in table:
                for name in ('subtotal', 'taxes'):
                    if name in tot['name'].lower():
                        total += clean_num(tot['cost'])
            inv['total'] = total


        inv['services'] = services
        yield  inv
