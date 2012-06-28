#!/usr/bin/env python
import time
import httplib
import urllib
import urllib2
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

from comcast.items import *

class ComcastSpiderBase(BaseSpider):
    _urls = settings.get('URLS')
    if isinstance(_urls, dict):
        vars().update(_urls)

    start_urls = [_LOGIN_URL]

    def __init__(self, *args, **kwargs):
        super(ComcastSpiderBase, self).__init__(*args, **kwargs)
        self.account_id = None
        self.invoices = []
        self.close_down = False
        self.username = None
        self.password = None
        self.username = 'sseshechela@comcast.net'
        self.password = 'Java9873%man'
        self.errors = []
        self.log = log

    def parse(self, response):
        if self.close_down:
            raise CloseSpider('No user id')
        if not self.username or not self.password:
            self.close_down = True
            self.log.msg("No credentials", level=log.ERROR)
            raise CloseSpider('No credentials')
        display = Display(visible=0, size=(800, 600))
        display.start()
        try:
            browser = webdriver.Firefox()
            browser.get(self._BILLS_URL)
            browser.find_element_by_id('user').click()
            browser.find_element_by_id('user').send_keys(self.username)
            browser.find_element_by_id('passwd').click()
            browser.find_element_by_id('passwd').send_keys(self.password)
            capt = None
            try:
                capt = browser.find_element_by_id('nucaptcha-media')
            except:
                pass
            if capt:
                cap_url = capt.get_attribute('src')
                gif = urllib2.urlopen(cap_url).read()
                status, captext = self.solve_captcha(gif)
                self.log.msg('%s %s' % (status, captext))
                if status == 'ERROR':
                    raise CloseSpider("Couldnt solve captcha. Error: %s" % captext)
                    return
            else:
                self.log.msg("No Captcha found")

            browser.find_element_by_name('passwd').submit()
            while True:
                try:
                    browser.find_element_by_id('loadingMessage')
                except:
                    break
                time.sleep(2)

            browser.save_screenshot('/tmp/log.png')
            source = browser.page_source
            soup = BeautifulSoup(source)
            fp = open('test.html', 'w')
            fp.write(soup.prettify())
            fp.close()
            div = soup.find('div',
                    id="ctl00_ContentArea_AccountDetails_PnlAccountInfo")
            if div:
                self.log.msg(div.text)
                acc = re.findall("([0-9]+)", div.text)
                if acc:
                    item = ComcastAccount()
                    item['account_id'] = acc[0]
                    yield item
            else:
                self.log.msg("No account block text")
            curitem = self.parse_comcast(browser)
            yield curitem
        except:
            raise
        finally:
            browser.quit()
            display.stop()

        return


    def solve_captcha(self, data):
        key = settings.get('CAPTCHA_KEY')
        if not key:
            return "ERROR", "INVALID CAPTCHA_KEY"
	boundary= '----------OmNaOmNaOmNamo'
	body = '''--%s
Content-Disposition: form-data; name="method"

post
--%s
Content-Disposition: form-data; name="key"

%s
--%s
Content-Disposition: form-data; name="file"; filename="capcha.gif"
Content-Type: image/gif

%s
--%s--

''' % (boundary, boundary, key, boundary, data, boundary)

	headers = {'Content-type' : 'multipart/form-data; boundary=%s' % boundary}
	h = httplib.HTTPConnection('antigate.com')
	h.request("POST", "/in.php", body, headers)
	resp = h.getresponse()
	data = resp.read()
	h.close()
        self.log.msg(data)
        if 'ERROR' in data:
            return "ERROR", "Error uploading captcha"
        cap_id= int(data.split('|')[1])
	time.sleep(5)

	res_url= 'http://antigate.com/res.php'
	res_url+= "?" + urllib.urlencode({'key': key, 'action': 'get', 'id': cap_id})
	while 1:
            res= urllib.urlopen(res_url).read()
            if res == 'CAPCHA_NOT_READY':
                time.sleep(1)
                continue
            break

	res = res.split('|')
	if len(res) == 2:
            return tuple(res)
	else:
            return ('ERROR', res[0])

    def parse_comcast(self, browser):
        """interface method for spider logic"""
        raise NotImplementedError("This method have to be overriden in derived class")

