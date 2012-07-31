#!/usr/bin/env python
import re
import os
import csv
import datetime
import time
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider
from scrapy.conf import settings

from BeautifulSoup import BeautifulSoup
from pyvirtualdisplay import Display
from selenium import webdriver

from att_busi.items import *

class TimeoutException(Exception):
    pass


class AttSpiderBase(BaseSpider):
    _urls = settings.get('URLS')
    name='s'
    if isinstance(_urls, dict):
        vars().update(_urls)

    start_urls = [_LOGIN_URL]

    def __init__(self, *args, **kwargs):
        super(AttSpiderBase, self).__init__(*args, **kwargs)
        self.account_id = None
        self.invoices = []
        self.close_down = False
        self.username = None
        self.password = None
        self.username = 'americct3'
        self.password = '!!pa66word'
        self.errors = []
        self.log = log
        self.pdf_folder = os.path.join('/tmp',
                     'tmppdf_att')

    def click_displayed(self, browser, cur, prev):
            tot = 0

            while not cur.is_displayed():
                prev.click()
                time.sleep(1)
                tot += 1
                if tot > 30:
                    raise TimeoutException("display error")
            cur.click()

    def parse(self, response):
        if self.close_down:
            self.errors.append('Bad credentials')
            raise CloseSpider('No user id')
        display = Display(visible=0, size=(800, 600))
        display.start()

        tmppdf = self.pdf_folder
        if not os.path.isdir(tmppdf):
            os.makedirs(tmppdf)
        fp = webdriver.FirefoxProfile()

        fp.set_preference("browser.download.folderList",2)
        fp.set_preference("browser.download.manager.showWhenStarting",False)
        fp.set_preference("browser.download.dir", tmppdf)
        fp.set_preference("browser.helperApps.neverAsk.saveToDisk",
            "application/csv, text/comma-separated-values, text/csv, application/octet-stream, text/plain")
        browser = webdriver.Firefox(firefox_profile=fp)

        try:
            browser.get(self._LOGIN_URL)
            browser.find_element_by_id('login').send_keys(self.username)
            browser.find_element_by_id('password').send_keys(self.password)
            browser.find_element_by_name('forForesee').click()
            browser.find_element_by_partial_link_text("Pay Your Bill").click()
            browser.switch_to_window(browser.window_handles[1])
            self.wait(browser)
            browser.find_element_by_id('2_td_2').click()
            self.wait(browser)
            browser.switch_to_frame('ibi_frame')
            time.sleep(1)
            srep = browser.find_element_by_xpath(
                    '//h1[contains(text(), "Standard Reports")]')
            mrep = browser.find_element_by_xpath(
                    '//h1[contains(text(), "Main Reports")]')
            chcr = browser.find_element_by_xpath(
                    '//h3[contains(text(), "Charges and Credits")]')
            detail = browser.find_element_by_xpath(
                    '//div[contains(text(), "Credits Detail")]')
            self.click_displayed(browser, mrep, srep)
            self.click_displayed(browser, chcr, mrep)
            self.click_displayed(browser, detail, chcr)


            time.sleep(12)
            browser.save_screenshot('/tmp/log.png')
            sel = browser.find_element_by_xpath('//select[@name="INV_DT"]')
            opts = sel.find_elements_by_tag_name('option')
            for opt in opts[:1]:
                sel.click()
                time.sleep(1)
                opt.click()
                time.sleep(1)
                selfmt = browser.find_element_by_xpath(
                        '//select[@id="OUTPUTFMT"]')
                tot = 0
                time.sleep(2)
                browser.save_screenshot('/tmp/ou%d.png' % tot)
                # while not selfmt.is_displayed():
                if not selfmt.is_displayed():
                    browser.find_element_by_xpath(
                            '//a[contains(text(), "Output Format")]').click()
                    time.sleep(5)
                    if not selfmt.is_displayed():
                        browser.find_element_by_xpath(
                                '//a[contains(text(), "Sorting")]').click()
                        time.sleep(5)
                        browser.find_element_by_xpath(
                                '//a[contains(text(), "Output Format")]').click()
                        time.sleep(5)
                    # tot += 5
                    # if tot > 30:
                    #     raise TimeoutException('page switch timeout')
                    # browser.save_screenshot('/tmp/ou%d.png' % tot)

                opt = selfmt.find_element_by_xpath('//option[@value="COMT"]')
                opt.click()
                time.sleep(2)

                submit_buts = browser.find_elements_by_xpath(
                        '//a[contains(@href, "submit_handler_rc")]')
                for b in submit_buts:
                    if b.is_displayed():
                        b.click()
                        break
                time.sleep(1)
                downl = b.find_elements_by_xpath(
                        '//a[contains(@href, "available_down")]')

                for b in downl:
                    if b.is_displayed():
                        b.click()
                        break
                time.sleep(1)
                loading_time = 0
                while loading_time<30:
                    el = browser.find_element_by_id('availableDL')
                    if el.text.strip():
                        break
                    time.sleep(2)
                    loading_time += 2
                time.sleep(2)
                browser.find_element_by_xpath(
                        '//input[contains(@onclick, "refreshPage")]').click()
                while loading_time<30:
                    el = browser.find_element_by_id('availableDL')
                    if el.text.strip():
                        break
                    time.sleep(2)
                    loading_time += 2

                time.sleep(1)
                first_tds = browser.find_elements_by_xpath(
                        '//div[@id="downloadDiv"]/table/tbody/tr[2]/td')
                if first_tds[0].text == u'Charges and Credits Detail':
                    ltimes = 0
                    while ltimes < 5:
                        first_tds = browser.find_elements_by_xpath(
                                '//div[@id="downloadDiv"]/table/tbody/tr[2]/td')
                        if first_tds[3].text == u'COMPLETE':
                            break
                        browser.find_element_by_xpath(
                                '//input[contains(@onclick, "refreshPage")]').click()
                        while loading_time<30:
                            el = browser.find_element_by_id('availableDL')
                            if el.text.strip():
                                break
                            time.sleep(2)
                            loading_time += 2
                        ltimes += 1
                    else:
                        self.log.msg("error downloading report")
                        print "error downl"
                    first_tds = browser.find_elements_by_xpath(
                            '//div[@id="downloadDiv"]/table/tbody/tr[2]/td')
                    if first_tds[3].text == u'COMPLETE':
                        first_tds[4].click()
                        time.sleep(3)
                        it = self.parse_csv_report()
                        if it:
                            print it
                            return browser
                        else:
                            print 'No lines'

        except Exception, e:
            print str(e)
            browser.save_screenshot('/tmp/last.png')
            raise

        finally:
            return browser
        #     browser.quit()
        #     display.stop()

    def parse_csv_report(self):
        files = os.listdir(self.pdf_folder)
        self.log.msg("files %s" % str(files))
        lines = []
        print files
        if files:
            csvread = csv.reader(open(os.path.join(self.pdf_folder,
                files[0])))
            lines = [l for l in csvread if l]
        # for f in files:
        #     os.remove(os.path.join(self.pdf_folder, f))
        return lines

    def parse_report(self, content):
        # not working method. too much cases to handle
        soup = BeautifulSoup(content)
        with open('1.html', 'w') as fp:
            fp.write(soup.prettify())
        div = soup.find('div', id='mainDivJQ')
        tables=div.findAll('table', recursive=False)
        trs = []
        for tabl in tables:
            trs += tabl.tbody.findAll('tr', recursive=False)
        data = {}
        self.curserv = []
        self.curlast = []
        self.testlast = []
        last = data
        for tr in trs:
            if tr.td.table:
                t = tr.td.table.text.strip()
                if not t:
                    continue
                if len(self.curserv) == 1:
                    precurlast = self.curlast[:]
                    last['service'] = self.curserv
                    try:
                        self.curlast.pop()
                        self.curlast.pop()
                        self.curlast.pop()
                        self.curlast.pop()
                    except:
                        print "Error pop in one service"
                        print precurlast
                        import ipdb
                        ipdb.set_trace()
                    self.curserv = []
                    dumpserv = True

                if t.startswith("Account:"):
                    ca = t.split()[1]
                    self.curlast = []
                    self.curlast.append(ca)
                elif t.startswith("Subaccount"):
                    csa =' '.join(t.split()[1:])
                    self.curlast.append(csa)
                else:
                    if t:
                        self.curlast.append(t)
            else:
                tds = tr.findAll('td', recursive=False)
                t = tds[0].text.strip()
                if t.lower() == 'service description':
                    continue
                res = t
                if 'Total: ' in t:
                    res = t.replace('Total:', '')
                if 'Account ' in t:
                    res = t.replace('Account ', '')
                if t == 'Total:' or 'total' in t.lower() or (res and res in
                        self.curlast):
                    if t == 'Total:':
                        last['service'] = self.curserv
                        self.curserv = []
                    try:
                        self.curlast.pop()
                    except:
                        pass
                else:
                    if t=="Account 281-955-4800-960":
                        import ipdb
                        ipdb.set_trace()
                    self.curserv.append(t)

            self.testlast.append(self.curlast[:])
            l = None
            for k in self.curlast:
                if l is None:
                    l = data
                if not k in l:
                    l[k] = {}
                l=l[k]

            if l is not None:
                last = l
        return data

    def wait(self, browser, lid='divPleaseWaitTD', max=30):
        time.sleep(2)
        loading_time = 0
        while True:
            if loading_time > max:
                self.errors.append("Loading page was too long - more than %d" % max)
                break
            try:
                browser.find_element_by_id(lid)
            except:
                break
            loading_time += 2
            time.sleep(2)

    def parse_att(self, response):
        """interface method for spider logic"""
        raise NotImplementedError("This method have to be overriden in derived class")

if __name__ == '__main__':
    a = AttSpiderBase()
    a.parse(1)
