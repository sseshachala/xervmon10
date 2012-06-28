#!/usr/bin/env python 
import re
import datetime
from scrapy.spider import BaseSpider
from scrapy.http import FormRequest, Request
from scrapy import log
from scrapy.exceptions import CloseSpider

from BeautifulSoup import BeautifulSoup

from comcast.items import *

from comcast_base import ComcastSpiderBase

class ComcastCurrentSpider(ComcastSpiderBase):
    name = 'comcast_current'

    def parse_comcast(self, response):
        pass
