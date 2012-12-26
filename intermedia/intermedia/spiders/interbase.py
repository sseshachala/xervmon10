import re
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

    def parse(self, response):
        if self.close_down:
            self.errors.append("Bad credentials")
            raise CloseSpider('Bad creds')
            return
        display = Display(visible=0, size=(800, 600))
        display.start()

        browser = webdriver.Firefox()
        browser.get(self._LOGIN_URL)
        browser.find_element_by_name('ctl00$ctlContent$txtAdministratorLogin').send_keys(self.username)
        browser.find_element_by_name('ctl00$ctlContent$txtAdministratorPassword').send_keys(self.password)
        browser.find_element_by_name('password').submit()
        cookies = browser.get_cookies()
        br_cookies = dict([(b['name'], b['value']) for b in cookies])

        browser.quit()
        display.stop()
        return Request(self)


    def after_login(self, response):
        from scrapy.shell import inspect_response
        inspect_response(response)
        soup = BeautifulSoup(re.sub('<html.*>', "<html>", response.body))
        error = soup.find("span", "error")
        if error:
            self.log.msg(error)
            self.close_down = True
            self.errors.append("Bad login %s" % error.text)
            raise CloseSpider("bad login")
            yield
        menu = soup.find('ul', id='Menu')
        account_str = re.search('\(ID ([0-9]+))\)', menu.text)
        if account_str and len(account_str.groups()):
            account = IntermediaAccount()
            account['account_id'] = account_str.group(0)
        else:
            raise CloseSpider("bad login")
            yield
        yield Request(self._URL_INVOICES, dont_filter=True,
                callback=self.parse_intermedia)

    def parse_intermedia(self, response):
        "To implement"
        raise NotImplementedError("You have to reimplement this method in derived class")


