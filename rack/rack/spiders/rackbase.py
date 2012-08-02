import re
import demjson
import datetime
import time
from BeautifulSoup import BeautifulSoup

from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.conf import settings
from scrapy.exceptions import CloseSpider

from rack.items import *


class RackSpiderBase(BaseSpider):
    _urls = settings.get('URLS')
    if isinstance(_urls, dict):
        vars().update(_urls)
    start_urls = [_URL_LOGIN]


    def __init__(self, *args, **kwargs):
        super(RackSpiderBase, self).__init__(*args, **kwargs)
        self.account_id = None
        self.username = None
        self.password = None
        self.close_down = False
        self.errors = []
        self.log = log

    def parse(self, response):
        if self.close_down:
            self.errors.append("Bad credentials")
            raise CloseSpider('No user id')
            return

        return [FormRequest.from_response(response, formname="LoginForm",
            formdata={"username": self.username, "password": self.password},
            callback=self.after_login)]

    def after_login(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        error = soup.find("div", "fieldError")
        if error:
            self.log.msg(error)
            self.close_down = True
            self.errors.append("Bad login %s" % error.text)
            raise CloseSpider("bad login")
            yield

        loginfo = soup.find("div", "logged-in-as")
        if not loginfo:
            yield
        loginfo_txt = "".join(loginfo.findAll(text=True)).strip()
        m = re.search("#([0-9]{4,})", loginfo_txt)
        if m and len(m.groups()):
            acc = RackAccount()
            acc['account_id'] = m.group(1)
            yield acc
        yield Request(self._URL_BILLING, dont_filter=True, callback=self.parse_rack)

    def parse_rack(self, response):
        "To implement"
        raise NotImplementedError("You have to reimplement this method in derived class")


    def _parse_js_table(self, data):
        "Return python dict"
        jsdic = None
        st = data.find('{')
        en = data.rfind('}')
        if not st or not en:
            return jsdic
        try:
            jsdic = demjson.decode(data[st:en+1])
        except:
            return

        def parse_val(jd):
            for k, v in jd.items():
                if v and isinstance(v, basestring) and v[0] in ('[', '{'):
                    try:
                        parsed = demjson.decode(v)
                    except:
                        continue
                    parsed_all = parse_val(parsed)
                    jd[k] = parsed_all
            return jd

        jsdic = parse_val(jsdic)
        names = [c['mappingName'] for c in jsdic['tableDefinition0']['columns']]
        items = [dict(zip(names, r)) for r in jsdic['tableData0']['rows']]
        return items


