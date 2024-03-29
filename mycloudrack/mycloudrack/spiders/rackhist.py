
import json
import copy
import datetime
from urlparse import urljoin

from scrapy.http import Request
from scrapy import log
from scrapy.conf import settings

from mycloudrack.spiders.rackbase import RackSpiderBase
from mycloudrack.items import RackInvoice, RackService, RackCredit


class RackSpiderHistorical(RackSpiderBase):
    name = "rack_hist"

    def parse_rack(self, response):
        log.msg('parse rack')
        yield Request(self._URL_INVOICES, callback=self.parse_invoice_list)

        urls = (
            (self._URL_SERVERS, self.parse_servers),
            (self._URL_SERVERS_ADD, self.parse_servers),
            (self._URL_BALANCER, self.parse_balancer),
            (self._URL_DNS, self.parse_dns),
            (self._URL_FILES, self.parse_files),
            (self._URL_DATABASE, self.parse_database),
            (self._URL_BACKUP, self.parse_backup)
        )
        for url, callback in urls:
            if '{region}' in url:
                for region in settings.get('REGIONS'):
                    meta = {'item': RackService(number=0, region=region)}
                    yield Request(url.format(region=region), callback=callback,
                            meta=meta)
            else:
                meta = {'item': RackService(number=0)}
                yield Request(url, callback=callback, meta=meta)

    def parse_dns(self, response):
        obj = self.json_to_obj(response.body)
        item = response.meta['item']
        item['name'] = 'dns'
        if obj:
            try:
                item['number'] += obj['totalEntries']
            except KeyError:
                pass
        yield item

    def parse_database(self, response):
        obj = self.json_to_obj(response.body)
        item = response.meta['item']
        item['name'] = 'databases'
        if obj:
            item['number'] += sum([1 for inst in obj['instances']
                if inst['status'] == 'ACTIVE'])
        yield item

    def parse_backup(self, response):
        yield Request(url=self._URL_BACKUP_DATA,
                callback=self.parse_backup_data, meta=response.meta)

    def parse_backup_data(self, response):
        obj = self.json_to_obj(response.body)
        item = response.meta['item']
        item['name'] = 'backup'

        if obj:
            item['number'] += len(obj)
        yield item

    def parse_files(self, response):
        obj = self.json_to_obj(response.body)
        item = response.meta['item']
        item['name'] = 'file containers'
        if obj:
            item['number'] += len(obj)
        yield item

    def parse_balancer(self, response):
        obj = self.json_to_obj(response.body)
        item = response.meta['item']
        item['name'] = 'load balancers'
        if obj:
            item['number'] += sum([1 for inst in obj['loadBalancers']
                if inst['status'] == 'ACTIVE'])
        yield item

    def parse_servers(self, response):
        obj = self.json_to_obj(response.body)
        item = response.meta['item']
        actItem = copy.deepcopy(item)
        actItem['name'] = 'active servers'
        errItem = copy.deepcopy(item)
        errItem['name'] = 'error servers'
        buildItem = copy.deepcopy(item)
        buildItem['name'] = 'build servers'
        if obj:
            servers = obj['servers']
            actItem['number'] += sum([1 for inst in servers
                if inst['status'] == 'Active'])
            buildItem['number'] += sum([1 for inst in servers
                if inst['status'] == 'Build'])
            errItem['number'] += sum([1 for inst in servers
                if inst['status'] == 'Error'])
        yield actItem
        yield buildItem
        yield errItem

    def parse_invoice_list(self, response):
        billing_info = self.json_to_obj(response.body)
        credit = RackCredit(amount=0)
        for info in billing_info['billing-summary']['item']:
            if info['type'].lower() == 'invoice':
                invoice_id = info['itemId']
                if info['itemStatus'].lower() == 'unpaid':
                    credit['amount'] += info['itemAmount']
                if invoice_id in self.old_invoices:
                    continue
                invoice_href = self._make_invoice_url(invoice_id)
                yield Request(invoice_href,
                        callback=self.parse_invoice)
        yield credit

    def parse_invoice(self, response):
        invoice_info = self.json_to_obj(response.body)
        inv_obj = RackInvoice()
        invoice = invoice_info['invoice']
        inv_obj['invoice_id'] = invoice['invoiceId']
        inv_obj['total'] = invoice['invoiceTotalPrice']
        inv_obj['services'] = invoice['invoiceItem']
        service = invoice['invoiceItem'][0]
        inv_obj['startdate'] = self.int_to_datetime(service['coverageStartDate'])
        inv_obj['enddate'] = self.int_to_datetime(service['coverageEndDate'])
        yield inv_obj

    def int_to_datetime(self, num):
        try:
            num = int(num)
            return datetime.datetime.fromtimestamp(num / 1000)
        except StandardError:
            return num



    def _make_invoice_url(self, invoice_id):
        return '%s%s' % (self._URL_INVOICE, invoice_id)

    def json_to_obj(self, json_body):
        try:
            obj = json.loads(json_body)
        except Exception, e:
            self.log.msg("Error parsing json: %s" % str(e))
        return obj
