
import re
import datetime
import demjson
from BeautifulSoup import BeautifulSoup

from scrapy.http import Request

from rackbase import RackSpiderBase
from rack.items import *


class RackSpiderCurrrent(RackSpiderBase):
    name = "rack_current"

    def parse_rack(self, response):
        yield Request(self._URL_SERVERS, callback=self.get_servers)
        yield Request(self._URL_API_KEY, callback=self.get_api_key)
        yield Request(self._URL_REPORTS, callback=self.get_reports)


    def get_reports(self, response):
        content = response.body
        soup = BeautifulSoup(re.sub('<!DOCTYPE(.*)>', '', content))
        cont = soup.find("div", id="content")
        racktotal = RackTotalUsage()
        if not cont:
            yield
        sections = cont.findAll("div", "section-content")
        header = sections[0]
        startdate = ''
        datesearch = re.search("last billing date of ([A-z 0-9,]+)", content)
        if datesearch and len(datesearch.groups()):
            msgbox = datesearch.group(1)
            try:
                startdate = datetime.datetime.strptime(msgbox, "%B %d, %Y")
            except:
                pass

        enddate = datetime.datetime.now()
        racktotal['startdate'] = startdate
        racktotal['enddate'] = enddate
        racktotal['invoice_id'] = ''
        racktotal['cost'] = ''
        yield racktotal

        for url in (self._URL_CLOUDSERVERS_CUR, self._URL_LOADBALANCERS_CUR,
                self._URL_CLOUDFILES_CUR):
            yield Request(url, callback=self._parse_usage, meta={'startdate':
                startdate, 'enddate': enddate})

        table = sections[1]
        js = table.script.text
        items = self._parse_js_table(js)
        for item in items:
            server = RackServers()
            server['startdate'] = startdate
            server['enddate'] = enddate
            server['invoice_id'] = ''
            server['usage'] = []
            server['startdate'] = startdate
            jsmap = (
                ('uptime', 'totalUptime'),
                ('bandwidth_in', 'bandwidthIn'),
                ('bandwidth_out', 'bandwidthOut'),
                ('charge', 'runningCharges')
                )
            try:
                server['name'] = item['serverName']
            except KeyError:
                server['name'] = ''
            use = {}
            for m in jsmap:
                try:
                    k = m[0]
                    v = m[1]
                    use[k] = item[v]
                    if k == 'charge':
                        server['cost'] = use[k]
                except:
                    continue
            server['usage'].append(use)
            try:
                server['cost'] = server['usage']['charge']
            except:
                pass
            yield server

    def get_api_key(self, response):
	key = demjson.decode(response.body)['apiKey']
        rkey = RackApiKey()
        rkey['key'] = key
	yield rkey

    def get_servers(self, response):
        content = response.body
        deldata = '\\"buttonBarHtml\\":\\"<button type=\\\\\\"button\\\\\\"                                onclick=\\\\\\"redirect(\'/CloudServers/AddNewCloudServer.do?dp=\');\\\\\\"                                class=\\\\\\"button add\\\\\\"><span>Add Server</span></button>                        <button id="">                            <span>Delete Selected</span></button>\\",'

        soup = BeautifulSoup(re.sub('<!DOCTYPE(.*)>', '', content))
        try:
            jscont = soup.find('div', 'section').script.text
        except:
            yield
        js = jscont.replace(deldata, '')
        data = self._parse_js_table(js)
        for serv in data:
            server = RackServerInfo()
            server['name'] = serv['serverName'][0]
            server['ip'] = serv['ipAddresses']
            server['id'] = serv['checkbox'][0]
            yield server

    def _parse_usage(self, response):
        meta = response.request.meta
        startdate = meta['startdate']
        enddate = meta['enddate']
        data = response.body
        soup = BeautifulSoup(data)
        keys = [d.text for d in soup("a", "usage-metric")]
        values = [d.text for d in soup("span", "usage-amount")]
        usage = dict(zip(keys, values))
        usage[u'type'] = soup.h3.text
        usage['startdate'] = startdate
        r = RackTotalUsageEntry()
        r['usage'] = usage
        yield r

