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

from myrack.items import *


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
        self.old_invoices = []
        self.log = log

    def parse(self, response):
        if self.close_down:
            self.errors.append("Bad credentials")
            raise CloseSpider('Bad creds')
            return

        return [FormRequest.from_response(response, formname="myrs-login",
            formdata={"account": self.account_id, "username": self.username, "password": self.password},
            callback=self.after_login)]

    def after_login(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        error = soup.find("div", "error")
        if error:
            self.log.msg(error)
            self.close_down = True
            self.errors.append("Bad login %s" % error.text)
            raise CloseSpider("bad login")
            yield

        loginfo = soup.find("div", id="myrs-account")
        if not loginfo:
            raise CloseSpider("bad login")
            yield
        yield Request(self._URL_INVOICES, dont_filter=True, callback=self.parse_rack)

    def parse_rack(self, response):
        "To implement"
        raise NotImplementedError("You have to reimplement this method in derived class")


