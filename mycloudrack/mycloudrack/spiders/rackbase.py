import re
import datetime
import time
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup

from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.conf import settings
from scrapy.exceptions import CloseSpider

from mycloudrack.items import *


class RackSpiderBase(BaseSpider):
    _urls = settings.get('URLS')
    _base_url = settings.get('BASE_URL')

    def __init__(self, *args, **kwargs):
        super(RackSpiderBase, self).__init__(*args, **kwargs)
        self.account_id = None
        self.username = "sudhi"
        self.password = "Java0man"
        self.close_down = False
        self.errors = []
        self.old_invoices = []
        self.log = log

    def start_requests(self):
        return [Request(self._base_url, dont_filter=True, callback=self.parse_first)]

    def parse_first(self, response):
        return Request(self._URL_LOGIN, dont_filter=True, callback=self.parse)

    def parse(self, response):
        if self.close_down:
            self.errors.append("Bad credentials")
            raise CloseSpider('Bad creds')
            return

        return [FormRequest.from_response(response,
            formdata={"username": self.username, "password": self.password},
            callback=self.after_login)]

    def after_login(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        error = soup.find("ul", "errorlist")
        if error:
            self.log.msg(error)
            self.close_down = True
            self.errors.append("Bad login %s" % error.text)
            raise CloseSpider("bad login")
            yield

        loginfo = soup.find("li", id="user-menu")
        if not loginfo:
            raise CloseSpider("bad login")
            yield
        loginfo_txt = "".join(loginfo.findAll(text=True)).strip()
        m = re.search("#([0-9]{4,})", loginfo_txt)
        if m and len(m.groups()):
            acc = RackAccount()
            acc['account_id'] = m.group(1)
            yield acc
        self.home_link = self.make_abs_link(soup.find('a',
            id='home_link')['href'])
        yield Request(self.home_link, dont_filter=True, callback=self.parse_rack)

    def make_abs_link(self, link):
        return urljoin(self._base_url, link)

    def parse_rack(self, response):
        "To implement"
        raise NotImplementedError("You have to reimplement this method in derived class")


