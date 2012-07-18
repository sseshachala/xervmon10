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
        self.username = 'sudhi@hooduku.com'
        self.password = 'Java0man'
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

        return [FormRequest.from_response(response, formnumber=0,
            formdata={"user[email]": self.username, "user[password]": self.password,
                },
            callback=self.after_login)]

    def after_login(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        error = soup.find("ul", "message-alert")
        account_num = soup.find('span', id="aux-nax-account-id")
        if not account_num:
            if error:
                self.log.msg(error.text)
            self.close_down = True
            raise CloseSpider("bad login")
            yield
        else:
           acc = HPCloudAccount()
           acc['account_id'] = account_num.text
           yield acc

        self.log.msg("Successfully logged in. Parsing now")
        yield Request(self._BILLS_URL, dont_filter=True,
                callback=self.parse_hpcloud)


    def parse_hpcloud(self, response):
        """interface method for spider logic"""
        raise NotImplementedError("This method have to be overriden in derived class")

