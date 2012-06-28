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
    name = 'comcast_history'

    def parse_comcast(self, browser):
        source = browser.page_source
        now = datetime.datetime.now()
        soup = BeautifulSoup(source)
        block = soup.find('div', 'bill_details_container')
        if not block:
            self.log.msg("No block found")
            return
        dates = block.find('span',
                id='ctl00_ContentArea_BillDetails_serviceBilledRange').text
        clean = dates.replace('for service from', '')
        dfrom, dto = clean.split('through')
        dformat = '%b. %d'
        curdate = datetime.datetime.strptime(dfrom.strip(), dformat)
        links = browser.find_elements_by_xpath('//div[@class="statement_list"]/ul/li/a')
        items = []
        displ_list = browser.find_element_by_xpath('//div[@class="statement_list"]/div[@class="select_display"]/a')
        for i, link in enumerate(links):
            if i == 0:
                continue
            displ_list.click()
            link.click()
            idate = browser.find_element_by_xpath('//div[@class="statement_list"]/div[@class="select_display"]/span')
            invdate = datetime.datetime.strptime(idate.text, '%B %d, %Y')
            if invdate == curdate or invdate in self.invoices:
                self.log.msg('Skipping invoice already in db %s' % invdate)
                continue
            browser.find_element_by_id('ctl00_ContentArea_BillDetails_billPdfButton').click()
            time.sleep(5)
            files = os.listdir(self.pdf_folder)
            self.log.msg("files %s" % str(files))
            if files:
                pdf_item = self.parse_pdf(os.path.join(self.pdf_folder, files[0]))
                for f in files:
                    os.remove(os.path.join(self.pdf_folder, f))
                items.append(pdf_item)

        return items

