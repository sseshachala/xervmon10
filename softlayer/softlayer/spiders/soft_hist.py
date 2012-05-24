#!/usr/bin/env python import re
import datetime
import urlparse
from BeautifulSoup import BeautifulSoup

from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider


from softlayer.items import *
from soft_base import SoftlayerSpiderBase

class SoftlayerHistSpider(SoftlayerSpiderBase):
    name = 'softlayer_hist'
    FORM_URL = (
    'https://manage.softlayer.com/Administrative/accountSummarySL/tabView')

    def parse_softlayer(self, response):
        """interface method for spider logic"""
        soup = BeautifulSoup(response.body)
        headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
                }

        data = {
                'data[SearchFilter][0][data]': '',
                'data[SearchFilter][0][method]': 'EXACT',
                'data[SearchFilter][0][field]': 'INVOICE_STATUS',
                'data[SearchFilter][1][data]': '',
                'data[SearchFilter][1][method]': 'EXACT',
                'data[SearchFilter][1][field]': 'INVOICE_TYPE',
                'data[SearchFilter][2][data]': '03/10/2004',
                'data[SearchFilter][2][method]': 'DATE_EXACT',
                'data[SearchFilter][2][field]': 'CREATE_FROM_DATE',
                'data[SearchFilter][3][data]': '05/23/2012', # now
                'data[SearchFilter][3][method]': 'DATE_EXACT',
                'data[SearchFilter][3][field]': 'CREATE_TO_DATE',
                'data[SearchFilter][4][data]': '',
                'data[SearchFilter][4][method]': 'CONTAINS',
                'data[SearchFilter][4][field]': 'INVOICE_ID'
                }

        yield FormRequest(self.FORM_URL, headers=headers,
                formdata=data, callback=self.parse_page)

    def parse_page(self, response):
        soup = BeautifulSoup(response.body)
        navdiv = soup.find('div',
                id='administrative_account_summary_sl_tab_view_administrative_get_invoice_list_pagination_header_nav')
        try:
            navlinks = navdiv.findAll('a', 'paginationNavLink')
        except AttributeError:
            navlinks = []
        yield self.parse_table(response)
        for a in navlinks:
            if not a.has_key('href'):
                continue
            href = a['href'].strip()
            self.log.msg(href)
            if href == '#':
                continue
            yield Request(urlparse.urljoin(self.FORM_URL, href), callback=self.parse_table)

    def parse_table(self, response):
        soup = BeautifulSoup(response.body)
        table = soup.find('table',
                id='administrative_getinvoicelist_0')
        a_links = soup.findAll('a', href=lambda t: 'xls' in t)
        for a in a_links:
            if a.has_key('href'):
                href = a['href']
                if not href or 'pending' in href.lower():
                    continue
                # Invoices always is 10 digit length
                invoice_num = href.split('/')[-2]
                invoice_num = (10 - len(invoice_num)) * '0' + invoice_num
                if invoice_num in self.invoices:
                    continue
                yield Request(urlparse.urljoin(self.FORM_URL, href),
                        callback=self._parse_invoice)