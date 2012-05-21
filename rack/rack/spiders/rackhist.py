
import re
import datetime
import demjson
from BeautifulSoup import BeautifulSoup

from scrapy.http import Request

from rackbase import RackSpiderBase
from rack.items import *


class RackSpiderHistorical(RackSpiderBase):
    name = "rack_hist"

    def parse_rack(self, response):
        yield Request(self._URL_BILLING_HISTORY, callback=self.get_billing_hist)

    def get_billing_hist(self, response):
        content = response.body
        lines = content.split("\n")
        for line in lines:
            if re.match("\s*tableData0", line):
                content = line
        pattern = re.compile("ViewInvoice.do\?invoiceID=(\d+)")
        invoice_ids = list(set(pattern.findall(content)))
        invoice_list = []
        invoice_data_list = []
        for id in invoice_ids:
            if id in self.old_invoices:
                continue
            url = self._URL_INVOICE + str(id)
            yield Request(url, callback=self._parse_invoice)

    def _parse_invoice(self, response):
        data = response.body
        startinv = endinv = None
        soup = BeautifulSoup(re.sub('<!DOCTYPE(.*)>', '', data))

        invoice = soup.find('table', 'invoice')
        if not invoice:
            return
        period = invoice.find(text=lambda x:"Coverage Period" in x)
        if period:
            startt = " ".join(period.split()[:-4])
            endt = " ".join(period.split()[-3:])
            startinv = datetime.datetime.strptime(startt,
                    "Coverage period: %b %d, %Y")
            endinv = datetime.datetime.strptime(endt,
                    "%b %d, %Y")
        try:
            invoice_id = invoice.find("div", "invoice-id").text
        except AttributeError:
            invoice_id = ''
        try:
            invoice_amount = invoice.find("span", "amount-due").text
        except AttributeError:
            invoice_amount = ''

        invoice_data = {
                'invoice_id': invoice_id,
                'cost': invoice_amount,
                'startdate': startinv,
                'enddate': endinv,
                }
        rackserv = RackServers()
        rackserv.update(invoice_data)
        yield rackserv

        rows = invoice.findAll('tr', 'itemRow')
        for row in rows:
            item = RackUsage()
            item['usagetype'] = row.td.strong.text
            dest = row.td.ul.li.text
            if dest:
                if 'Server name' in dest:
                    split = dest.split('Server name:')
                    item['server'] = split[-1].strip()
                    usage = re.search("([0-9.]+)", split[0])
                else:
                    item['server'] = ''
                    usage = re.search("([0-9.]+)", dest)
                if usage and len(usage.groups()):
                    item['usagevalue'] = usage.group(1)
                else:
                    item['usagevalue'] = ''
                try:
                    service = row.td.nextSibling.nextSibling.text.split("-")
                    item['service'] = service[0].strip()
                    item['operation'] = service[1].strip()
                except:
                    item['service'] = item['operation'] = ''
                item['cost'] = ''
                try:
                    item['cost'] = row.findAll('td', 'even')[2].strong.text
                except:
                    pass

                item['startdate'] = startinv
                item['enddate'] = endinv
                item['invoice_id'] = invoice_id
                yield item





