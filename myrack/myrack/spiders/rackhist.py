
import re
from dateutil.relativedelta import relativedelta
import datetime
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup

from scrapy.http import Request
from scrapy import log

from pdfminer.pdfparser import PDFDocument, PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter, process_pdf
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from cStringIO import StringIO


from rackbase import RackSpiderBase
from myrack.items import *


class RackSpiderHistorical(RackSpiderBase):
    name = "rack_hist"

    def parse_rack(self, response):
        log.msg('parse rack')
        soup = BeautifulSoup(response.body)
        table = soup.find('table', 'myrs-datagrid')
        invoices_tr = table.findAll('tr', 'invoice')
        for tr in invoices_tr:
            tds = tr.findAll('td', recursive=False)
            inv = RackInvoice()
            inv['invoice_id'] = tds[2].text.strip()
            inv['account_id'] = self.account_id
            if  inv['invoice_id'] in self.old_invoices:
                continue
            inv['enddate'] = datetime.datetime.strptime(tds[3].text.strip(), '%Y-%m-%d')
            inv['startdate'] = inv['enddate'] + relativedelta(months=-1)
            inv['total'] = tds[4].text.strip().replace('$', '')
            link = tds[2].a['href']
            log.msg(link)
            meta = dict(inv=inv)
            yield Request(urljoin(response.url, link), callback=self.parse_pdf, meta=meta)




    def parse_pdf(self, response):
        meta = response.request.meta
        inv = meta['inv']
        data = StringIO(response.body)
        pdfstr = self.pdf_to_string(data) 
        lines = [l for l in pdfstr.split('\n') if l]
        data = {}
        services = {}
        cur_point = None
        totals = []
        services_num = 0
        cur_service_line = 0
        cur_service = 0
        for line in lines:
            if line == 'Total':
                cur_point = 'total'
                continue
            elif line == 'Reference No.':
                services_num = len(totals) - 4
                cur_point = None
                continue
            elif line == 'Unit Price':
                cur_point = 'services'
                continue
            elif line == 'Subtotal:':
                cur_point = None
                continue
            if cur_point == 'total':
                totals.append(line)

            elif cur_point == 'services':
                if not cur_service in services:
                    services[cur_service] = {}
                services[cur_service][cur_service_line] = line
                cur_service_line += 1
                if cur_service_line % 4 == 0:
                    cur_service_line = 0
                    cur_service += 1

        inv['services'] = []
        for serv in services.values():
            item = {}
            item['service'] = serv[0]
            item['name'] = serv[1]
            item['qty'], item['uom'] = serv[2].split()
            item['cost'] = serv[3]
            inv['services'].append(item)
        yield inv

                



        
    def pdf_to_string(self, pdfpath):
        rsrcmgr = PDFResourceManager()
        stringio = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, stringio, codec=codec, laparams=laparams)
        process_pdf(rsrcmgr, device, pdfpath)
        device.close()

        pdfstr = stringio.getvalue()
        stringio.close()
        return pdfstr



