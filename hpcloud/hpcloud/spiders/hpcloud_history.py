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

from hpcloud.items import *

from hpcloud_base import HPCloudSpiderBase

class HPCloudHistorySpider(HPCloudSpiderBase):
    name = 'hpcloud_history'

    def parse_hpcloud(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        year_select = soup.find('select', id='billing_year')
        try:
            options = year_select.findAll('option')
        except AttributeError:
            options = None
        if options is None or len(options) == 1:
            yield self.parse_list_page(response)
        else:
            for option in options:
                href = option['value']
                yield Request(urlparse.urljoin(response.url, href),
                        dont_filter=True, callback=self.parse_list_page)


    def parse_list_page(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        inv_table = soup.find('table', 'table_data')
        inv_links = inv_table.findAll('a', id=re.compile("invoiceDate"))
        log.msg(str(inv_links))
        for link in inv_links:
            href = link.attrMap.get('href')
            if not href:
                continue
            yield Request(urlparse.urljoin(response.url, href), dont_filter=True, callback=self.parse_invoice)

    def parse_invoice(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        inv = HPCloudData()
        content = soup.find('section', id='content')
        header = content.header
        dat = header.findAll('strong')
        log.msg(dat)
        startdate = dat[1].text
        enddate = dat[2].text
        templ = '%B %d, %Y'
        inv['startdate'] = datetime.datetime.strptime(startdate, templ)
        inv['enddate'] = datetime.datetime.strptime(enddate, templ)
        inv['invoice_number'] = dat[3].text
        if inv['invoice_number'] in self.invoices:
            log.msg("Skipping. Invoice number already in db")
            return
        services = {}
        sections = content.findAll('section')
        totals = []
        for section in sections:
            if section.get('id') == u'invoice_totals':
                tb = section.tbody
                if not tb:
                    continue
                for tr in tb.findAll('tr'):
                    tds = tr.findAll('td')
                    tds = map(lambda x: x.text.lower().strip(), tds)
                    us = {}
                    us['name'] = tds[0]
                    us['cost'] = tds[1]
                    totals.append(us)
                tf = section.tfoot
                for tr in tf.findAll('tr'):
                    tds = tr.findAll('td')
                    tds = map(lambda x: x.text.lower().strip(), tds)
                    if tds[0] == 'amount due':
                        inv['total'] = tds[1]
            else:
                usage = []
                tb = section.tbody
                if not tb:
                    continue
                for tr in tb.findAll('tr'):
                    tds = tr.findAll('td')
                    tds = map(lambda x: x.text.lower().strip(), tds)
                    us = {}
                    us['name'] = tds[0]
                    us['quan'] = tds[1]
                    us['cost'] = tds[2]
                    usage.append(us)
                name = section.h2.text
                services[name] = usage

        inv['services'] = services
        inv['totals'] = totals
        yield inv

