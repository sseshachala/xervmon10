#!/usr/bin/env python import re
import datetime
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider

from BeautifulSoup import BeautifulSoup

from softlayer.items import *
from soft_base import SoftlayerSpiderBase

class SoftlayerCurrentSpider(SoftlayerSpiderBase):
    name = 'softlayer_current'

    _URL_NEXT_INVOICE = "https://manage.softlayer.com/Administrative/showNextInvoice"
    _URL_NEXT_INVOICE_XLS = "https://manage.softlayer.com/Administrative/showNextInvoice/xls"
    _URL_BANDWIDTH = 'https://manage.softlayer.com/PublicNetwork/bandwidth'


    def parse_softlayer(self, response):
        """interface method for spider logic"""
        yield Request(self._URL_NEXT_INVOICE_XLS, callback=self._parse_invoice,
                meta={'invoice_id': self.CURRENT_INVOICE})
        yield Request(self._URL_BANDWIDTH, callback=self.parse_bandwidth)

    def parse_bandwidth(self, response):
        soup = BeautifulSoup(response.body)
        table = soup.find('table', id="bandwidth_hardwarelist_public_0")
        trs = table.tbody.findAll('tr')
        for tr in trs:
            tds = tr.findAll('td')
            if len(tds) < 8:
                continue
            item = SoftlayerBandwidth()
            item['server_name'] = tds[0].text.lower()
            item['ip'] = tds[1].text
            item['allocated'] = tds[4].text
            item['bandwidth_current'] = tds[5].text
            item['bandwidth_projected'] = tds[6].text
            for k, v in item.items():
                item[k] = v.replace("&nbsp;", '').strip()
            yield item

