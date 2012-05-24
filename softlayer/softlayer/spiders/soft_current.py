#!/usr/bin/env python import re
import datetime
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider

from softlayer.items import *
from soft_base import SoftlayerSpiderBase

class SoftlayerCurrentSpider(SoftlayerSpiderBase):
    name = 'softlayer_current'

    _URL_NEXT_INVOICE = "https://manage.softlayer.com/Administrative/showNextInvoice"
    _URL_NEXT_INVOICE_XLS = "https://manage.softlayer.com/Administrative/showNextInvoice/xls"


    def parse_softlayer(self, response):
        """interface method for spider logic"""
        yield Request(self._URL_NEXT_INVOICE_XLS, callback=self._parse_invoice)

