#!/usr/bin/env python 
import re
import datetime
import urlparse

from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider

from BeautifulSoup import BeautifulSoup

from att.items import *

from att_base import AttSpiderBase

class AttHistorySpider(AttSpiderBase):
    name = 'att_history'

    def parse_att(self, response):
        content = response.body
        soup = BeautifulSoup(content)
        with open('bill.html', 'w') as fp:
            fp.write(soup.prettify())
        links = [urlparse.urljoin(self._BASE_URL, a['href']) for a  in
                soup.findAll('a', href=re.compile('billSummary'))]
        for link in links:
            yield Request(link, cookies=response.request.cookies,
                    callback=self.parse_bill)


    def parse_bill(self, response):
        soup = BeautifulSoup(response.body.replace('&nbsp;',''))
        bill = AttBill()
        periodsel = soup.find('select', {'name': 'stmtID'})
        periodraw = periodsel.find('option', {'selected': 'selected'}).text
        frraw, toraw = map(lambda x: x.strip(), periodraw.split('-'))
        dformat = '%B %d, %Y'
        bill['startdate'] = datetime.datetime.strptime(frraw, dformat)
        if bill['startdate'] in self.invoices:
            self.log.msg('Invoice already in db. Skipping...')
            yield
        bill['enddate'] = datetime.datetime.strptime(toraw, dformat)
        blocks = soup.findAll('div', 'rel box')
        bill['nums'] = {}
        bill['charges'] = {}
        tables = []
        services = []
        charges = soup.find('div', id='accountChargesPDO')
        if charges:
            tables = charges.findAll('table')
            bill['charges']['total'] = tables[-1].findAll('strong')[1].text
            #last one is total
            tables = tables[:-1]
        for table in tables:
            service = {}
            namediv = table.findPrevious('div', 'MarLeft25').findPreviousSibling('div')
            name, charge = map(lambda t: t.text, namediv.findAll('b'))
            trs = table.tbody.findAll('tr')
            service['usage'] = []
            for tr in trs:
                us = {}
                us['info'] = tr.td.text
                us['info2'] = tr('td')[1].text
                us['cost'] = tr('td')[-1].text
                service['usage'].append(us)
            service['name'] = name
            service['total'] = charge
            services.append(service)
        bill['charges']['services'] = services
        nums = soup.findAll('div', id=re.compile('^toggleCTNstrWirelessCounter'))
        number_usage = []
        for num in nums:
            numu = {}
            namediv = num.findPreviousSibling('div')
            numu['cost'] = namediv.find('span', 'amount').text
            number = namediv.find('b').text
            numu['number'] = re.findall('([0-9-]{7,})', number)[0]
            tables = num.findAll('table')
            services = []
            for table in tables[:-1]:
                service = {}
                namediv = table.findPrevious('div', 'toggleHidden').findPreviousSibling('div')
                name = namediv.find('a').text
                charge = namediv.find('span', 'amount').text
                if not table.tbody:
                    continue
                trs = table.tbody.findAll('tr')
                service['usage'] = []
                for tr in trs:
                    us = {}
                    if len(tr('td')) < 2:
                        continue
                    us['info'] = tr.td.text
                    If len(tr('td')) > 2:
                        us['info2'] = tr('td')[1].text
                    us['cost'] = tr('td')[-1].text
                    service['usage'].append(us)
                service['name'] = name
                service['total'] = charge
                services.append(service)
            numu['services'] = services
            number_usage.append(numu)
        bill['nums'] = number_usage

        yield bill
