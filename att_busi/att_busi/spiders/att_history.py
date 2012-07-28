#!/usr/bin/env python 
import re
import datetime
from dateutil.relativedelta import relativedelta
import urlparse

from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider

from BeautifulSoup import BeautifulSoup

from att_busi.items import *

from att_base import AttSpiderBase

class AttHistorySpider(AttSpiderBase):
    name = 'att_history'


    def parse_att(self, response):
        pass
