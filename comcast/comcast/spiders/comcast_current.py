#!/usr/bin/env python 

import os
import re
import time
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
            self.log.msg("No block found")
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
        results = []
        for li in lis:
            result = {}
            n = li.text
            amount = li.find('span', 'amount').text
            n = n.replace(amount, '')
            result['name'] = n
            result['cost'] = amount
            results.append(result)
            if n.lower() == 'total bill':
                item['total'] = amount
        item['bill'] = results
        browser.find_element_by_id('ctl00_ContentArea_BillDetails_latestbillPdfButton').click()
        time.sleep(5)
        files = os.listdir(self.pdf_folder)
        self.log.msg("files %s" % str(files))
        if files:
            pdf_item = self.parse_pdf(os.path.join(self.pdf_folder, files[0]))
            self.clean_pdf_folder()
            item['services'] = pdf_item['services']

        return [item]

