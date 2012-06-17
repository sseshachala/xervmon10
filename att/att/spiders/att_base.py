#!/usr/bin/env python
import re
import datetime
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider
from scrapy.conf import settings

from BeautifulSoup import BeautifulSoup
from pyvirtualdisplay import Display
from selenium import webdriver

from att.items import *

class AttSpiderBase(BaseSpider):
    _urls = settings.get('URLS')
    if isinstance(_urls, dict):
        vars().update(_urls)

    _LOGIN_URL = (
        'https://www.att.com/olam/loginAction.olamexecute?customerType=W')
    _DETAIL_URL = (
        'https://www.att.com/olam/passthroughAction.myworld?actionType=ViewBillDetails')
    _LOGIN_SUBMIT_URL = (
        'https://myattdx15.att.com/commonLogin/igate_wam/multiLogin.do')
    start_urls = [_LOGIN_URL]

    def __init__(self, *args, **kwargs):
        super(AttSpiderBase, self).__init__(*args, **kwargs)
        self.account_id = None
        self.invoices = []
        self.close_down = False
        self.username = None
        self.password = None
        self.username = '4082039960'
        self.password = 'Java0man'
        self.errors = []
        self.log = log

    def parse(self, response):
        display = Display(visible=0, size=(800, 600))
        display.start()

        browser = webdriver.Firefox()
        browser.get(self._LOGIN_URL)
        browser.find_element_by_name('userid').send_keys(self.username)
        browser.find_element_by_name('password').send_keys(self.password)
        browser.find_element_by_name('password').submit()
        cookies = browser.get_cookies()
        browser.save_screenshot('/tmp/log.png')
        browser.quit()
        display.stop()

        br_cookies = dict([(b['name'], b['value']) for b in cookies])

        if self.close_down:
            raise CloseSpider('No user id')
        if not self.username or not self.password:
            self.close_down = True
            self.log.msg("No credentials", level=log.ERROR)
            raise CloseSpider('No credentials')
        return Request(self._DETAIL_URL, cookies=br_cookies,
                callback=self.after_login)

    def after_login(self, response):
        content = response.body
        self.log.msg(content)
        soup = BeautifulSoup(content)
        try:
            div = soup.find('div', id='dbUserName')
            it = AttAccount()
            it['account_id'] = div.text
            yield it
        except:
            self.close_down =True
            raise CloseSpider('No account id')
        if error:
            self.log.msg("Error login")
            self.close_down = True
            raise CloseSpider("bad login")
        self.log.msg("Go to parsing")
        acid = div
        if not acid:
            self.close_down = True
            raise CloseSpider("bad login")
        yield Request(self._BILLING_URL, dont_filter=True,
                callback=self.parse_softlayer)

    def parse_att(self, response):
        """interface method for spider logic"""
        raise NotImplementedError("This method have to be overriden in derived class")

