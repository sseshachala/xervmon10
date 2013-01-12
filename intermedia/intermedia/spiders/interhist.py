import re
from dateutil.relativedelta import relativedelta
import datetime
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup

from scrapy.http import Request
from scrapy import log


from interbase import IntermediaSpiderBase
from intermedia.items import *


class IntermediaSpiderHistorical(IntermediaSpiderBase):
    name = "intermedia_hist"

    def parse_intermedia(self, response):
        print 'parse starting'
        soup = BeautifulSoup(response.body)
        yield
