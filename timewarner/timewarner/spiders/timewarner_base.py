#!/usr/bin/env python

import re
import datetime
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider
from scrapy.conf import settings

from BeautifulSoup import BeautifulSoup

from timewarner.items import *

class TimewarnerSpiderBase(BaseSpider):
    _urls = settings.get('URLS')
    if isinstance(_urls, dict):
        vars().update(_urls)

    start_urls = [_LOGIN_URL]


    def __init__(self, *args, **kwargs):
        super(TimewarnerSpiderBase, self).__init__(*args, **kwargs)
        self.account_id = None
        self.username = None
        self.password = None
        self.close_down = False
        self.errors = []
        self.invoices = []
        self.log = log

    def parse(self, response):
        if self.close_down:
            raise CloseSpider('No user id')
            return
        if not self.username or not self.password:
            self.close_down = True
            self.log.msg("No credentials", level=log.ERROR)
            raise CloseSpider('No credentials')
            return

        return [FormRequest.from_response(response, formname="form1",
            formdata={"txtUserName": self.username, "txtPassword": self.password,
                "__EVENTTARGET": "GO", "__EVENTARGUMENT": "", "__LAST_FOCUS":
                ""},
            callback=self.after_login)]

    def after_login(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        error = soup.find("span", "error")
        logname = soup.find('span', id="ctl00_lbUser")
        if not logname:
            if error:
                self.log.msg(error.text)
            self.close_down = True
            raise CloseSpider("bad login")
            yield

        self.log.msg("Successfully logged in. Parsing now")
        yield Request(self._BILLS_URL, dont_filter=True,
                callback=self.parse_timewarner)


    def parse_timewarner(self, response):
        """interface method for spider logic"""
        raise NotImplementedError("This method have to be overriden in derived class")



