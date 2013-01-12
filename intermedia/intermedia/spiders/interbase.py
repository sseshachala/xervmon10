#!/usr/bin/env python

import re
import time
from BeautifulSoup import BeautifulSoup

from pyvirtualdisplay import Display
from selenium import webdriver

from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.conf import settings
from scrapy.exceptions import CloseSpider

from intermedia.items import *


class IntermediaSpiderBase(BaseSpider):
    _urls = settings.get('URLS')
    if isinstance(_urls, dict):
        vars().update(_urls)
    start_urls = [_URL_LOGIN]


    def __init__(self, *args, **kwargs):
        super(IntermediaSpiderBase, self).__init__(*args, **kwargs)
        self.username = None
        self.password = None
        self.username = 'sseshachala@americanmidstream.com'
        self.password = 'Pipeline101'
        self.close_down = False
        self.errors = []
        self.old_invoices = []
        self.log = log
        self.browser = self.display = None

    def __del__(self):
        if self.browser:
            self.browser.close()
        if self.display:
            self.display.stop()

    def parse(self, response):
        if self.close_down:
            self.errors.append("Bad credentials")
            raise CloseSpider('Bad creds')
            return
        display = Display(visible=0, size=(800, 600))
        display.start()

        browser = webdriver.Firefox()
        browser.get(self._URL_LOGIN)
        browser.find_element_by_name('ctl00$ctlContent$txtAdministratorLogin').send_keys(self.username)
        browser.find_element_by_name('ctl00$ctlContent$txtAdministratorPassword').send_keys(self.password)
        browser.find_element_by_id('ctl00_ctlContent_btnAdministratorLogin').click()
        time.sleep(3)
        cookies = browser.get_cookies()
        br_cookies = dict([(b['name'], b['value']) for b in cookies])
        self.browser = browser
        self.display = display
        import ipdb; ipdb.set_trace()

        return Request(self._URL_ACCOUNT, cookies=br_cookies,
                callback=self.after_login)

    def after_login(self, response):
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        error = soup.find("span", "error")
        if error:
            self.log.msg(error)
            self.close_down = True
            self.errors.append("Bad login %s" % error.text)
            raise CloseSpider("bad login")
            yield
        menu = soup.find('div', 'Title')
        if not menu:
            raise CloseSpider("bad login")
            yield
        account_str = re.search('\(ID ([0-9]+)\)', menu.text)
        if account_str and len(account_str.groups()):
            account = IntermediaAccount()
            account['account_id'] = account_str.group(0)
        else:
            raise CloseSpider("bad login")
            yield

        import ipdb; ipdb.set_trace()
        yield Request(self._URL_INVOICES, dont_filter=True,
                cookies=response.request.cookies,
                callback=self.parse_intermedia)

    def parse_intermedia(self, response):
        "To implement"
        raise NotImplementedError("You have to reimplement this method in derived class")


