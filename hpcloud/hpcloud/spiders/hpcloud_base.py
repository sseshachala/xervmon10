#!/usr/bin/env python

import re
import datetime
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider
from scrapy.conf import settings

from BeautifulSoup import BeautifulSoup

from hpcloud.items import *

class HPCloudSpiderBase(BaseSpider):
    _urls = settings.get('URLS')
    if isinstance(_urls, dict):
        vars().update(_urls)

    start_urls = [_LOGIN_URL]


    def __init__(self, *args, **kwargs):
        super(HPCloudSpiderBase, self).__init__(*args, **kwargs)
        self.account_id = None
        self.username = None
        self.password = None
        self.close_down = False
        self.errors = []
        self.invoices = []
        self.log = log

    def parse(self, response):
        if self.close_down:
            self.errors.append("Bad Credentials")
            raise CloseSpider('No user id')
            return

        return [FormRequest.from_response(response, formnumber=0,
            formdata={"user[username]": self.username, "user[password]": self.password,
                },
            callback=self.after_login)]

    def after_login(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        error = soup.find("ul", "message-alert")
        if error:
            self.errors.append("Bad login %s" % error.text)
            self.log.msg(error.text)
            raise CloseSpider("bad login")
            yield
        yield Request(self._BILLS_URL, callback=self.account_page_parse)

    def account_page_parse(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        account_num = soup.find('span', id="accountId")
        if not account_num:
            self.close_down = True
            self.errors.append("Bad login cant find accountid")
            raise CloseSpider("bad login")
            yield
        else:
           acc = HPCloudAccount()
           acc['account_id'] = account_num.text.strip()
           yield acc

        self.log.msg("Successfully logged in. Parsing now")
        yield Request(self._BILLS_URL, dont_filter=True,
                callback=self.parse_hpcloud)


    def parse_hpcloud(self, response):
        """interface method for spider logic"""
        raise NotImplementedError("This method have to be overriden in derived class")

