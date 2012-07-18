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

from hpcloud_base import hpcloudSpiderBase

class HPCloudHistorySpider(hpcloudSpiderBase):
    name = 'hpcloud_history'

    def parse_hpcloud(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        inv_table = soup.find('table', 'table_data')
        inv_links = inv_table.findAll('a', lambda x: 'invoiceDate' in x.id)
        log.msg(str(inv_links))
        return
