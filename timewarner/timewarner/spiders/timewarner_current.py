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
        enddate_span = soup.find('span', id='ctl00_MasterMainContentPlaceHolder_ctrlSnapshot_disclaimerLabel')
        try:
            enddate = re.findall('([0-9]{1,2}/[0-9]{1,2}/[0-9]{4} [0-9]{1,2}:[0-9]{1,2} [ap]\.m\.)', enddate_span.text)[0]
            item['enddate'] = datetime.datetime.strptime(enddate.replace('.', '').upper(), '%m/%d/%Y %I:%M %p')
        except:
            pass
        acc = TimewarnerAccount()
        acc['account_id'] = opt_acc.text
        yield acc
        item['total'] = soup.find('span',
                id='ctl00_MasterMainContentPlaceHolder_ctrlSnapshot_currentChargesLabel').text.strip()
        item['tax'] = soup.find('span',
                id='ctl00_MasterMainContentPlaceHolder_ctrlSnapshot_currentTaxesLabel').text.strip()
        yield item
