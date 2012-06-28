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

from pdfminer.pdfparser import PDFDocument, PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter, process_pdf
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.layout import LAParams
from cStringIO import StringIO

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
        self.pdf_folder = 'tmppdf'
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
        tmppdf = self.pdf_folder
        if not os.path.isdir(tmppdf):
            os.mkdir(tmppdf)
        fp = webdriver.FirefoxProfile()

        fp.set_preference("browser.download.folderList",2)
        fp.set_preference("browser.download.manager.showWhenStarting",False)
        fp.set_preference("browser.download.dir", tmppdf)
        fp.set_preference("browser.helperApps.neverAsk.saveToDisk",
            "application/pdf")

        try:
            browser = webdriver.Firefox(firefox_profile=fp)
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
            items = self.parse_comcast(browser)
            for item in items:
                yield item
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
            if res == 'CAPCHA_NOT_READY': time.sleep(1)
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

    def parse_pdf(self, pdfpath):
        string = self.pdf_to_string(pdfpath)
        isservice = False
        isservice_cost = False
        lines = string.split('\n')
        services = []
        services_cost = []
        for i, line in enumerate(lines):
            if not services and line == 'New Charges Summary':
                isservice = True
                continue
            if line == 'Total New Charges':
                isservice = False
                if services:
                    services.append('Total')
            if (not isservice and services and not services_cost and
                    not re.search('[^0-9-\.]', line) and
                  not lines[i+1]):
                isservice_cost = True
            if isservice_cost and '$' in line:
                isservice_cost = False
                services_cost.append(line)

            if isservice and line:
                services.append(line)

            if isservice_cost and line:
                services_cost.append(line)
        print services, services_cost
        self.log.msg(lines)
        return lines



    def pdf_to_string(self, pdfpath):
        rsrcmgr = PDFResourceManager()
        stringio = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, stringio, codec=codec, laparams=laparams)
        with open(pdfpath, 'rb') as fp:
            process_pdf(rsrcmgr, device, fp)
        device.close()

        pdfstr = stringio.getvalue()
        stringio.close()
        return pdfstr

