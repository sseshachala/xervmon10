#!/usr/bin/env python 
import re
import datetime
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider

from BeautifulSoup import BeautifulSoup

from comcast.items import *

from comcast_base import ComcastSpiderBase

class ComcastCurrentSpider(ComcastSpiderBase):
    name = 'comcast_current'

    def parse_comcast(self, browser):
        source = browser.page_source
        now = datetime.datetime.now()
        soup = BeautifulSoup(source)
        block = soup.find('div', 'bill_details_container')
        if not block:
            return
        item = ComcastCurrent()
        dates = block.find('span',
                id='ctl00_ContentArea_BillDetails_serviceBilledRange').text
        clean = dates.replace('for service from', '')
        dfrom, dto = clean.split('through')
        dformat = '%b. %d'
        date_from = datetime.datetime.strptime(dfrom.strip(), dformat)
        date_to = datetime.datetime.strptime(dto.strip(), dformat)
        date_to = date_to.replace(year = now.year)
        date_from = date_from.replace(year = now.year)
        if now.month == 1 and date_from.month == 12:
            date_from = date_from.replace(year = now.year - 1)
        if now.month == 12 and date_to.month == 1:
            date_to = date_to.replace(year = now.year + 1)
        item['startdate'] = date_from
        item['enddate'] = date_to
        bill = block.find('ul', 'billing_list')
        lis = bill.findAll('li')[0:-1]
        results = {}
        for li in lis:
            n = li.text
            amount = li.find('span', 'amount').text
            n = n.replace(amount, '')
            results[n] = amount
        item['bill'] = results
        item['total'] = results['Total bill']
        return item

