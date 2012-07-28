#!/usr/bin/env python 
import re
import datetime
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider

from BeautifulSoup import BeautifulSoup

from att_busi.items import *

from att_base import AttSpiderBase

class AttCurrentSpider(AttSpiderBase):
    name = 'att_current'

    def parse_att(self, response):
        pass
