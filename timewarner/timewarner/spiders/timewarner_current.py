#!/usr/bin/env python 

import re
import datetime
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider

from BeautifulSoup import BeautifulSoup

from timewarner.items import *


from timewarner_base import TimewarnerSpiderBase

class TimewarnerCurrentSpider(TimewarnerSpiderBase):
    name = 'timewarner_current'

    def parse_timewarner(self, response):
        yield Request(self._CUR_BILL, callback=self.parse_current)

    def parse_current(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        item = TimewarnerCurrent()
        select_acc = soup.find('select', {'name': 'ctl00$MasterMainContentPlaceHolder$accountDropDown'})
        opt_acc = select_acc.find('option', selected="selected")
        acc = TimewarnerAccount()
        acc['account_id'] = opt_acc.text
        yield acc
        item['total'] = soup.find('span',
                id='ctl00_MasterMainContentPlaceHolder_ctrlSnapshot_currentChargesLabel').text.strip()
        item['tax'] = soup.find('span',
                id='ctl00_MasterMainContentPlaceHolder_ctrlSnapshot_currentTaxesLabel').text.strip()
        yield item
