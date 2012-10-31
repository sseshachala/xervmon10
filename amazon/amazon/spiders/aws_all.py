import datetime
import calendar
from BeautifulSoup import BeautifulSoup

from scrapy.http import Request, FormRequest

from amazon.items import AmazonCharges
from aws import AwsSpiderBase

class AwsSpiderAll(AwsSpiderBase):
    name = 'aws_hist'

    def parse_aws(self, response):
        if not self.check_permission(response):
            return
        soup = BeautifulSoup(response.body)
        sel = soup.findAll("select")[1]
        opts = sel.findChildren()
        ret = []
        for o in opts:
            t = "".join(o.findAll(text=True))
            if t == "Current Statement":
                pass
            else:
                year = t.split(", ")[1]
                months = t.split(", ")[0]
                start = months.split(" - ")[0]
                end = months.split(" - ")[1]
                sdate = datetime.datetime.strptime("%s %s" % (start, year), "%B %d %Y")
                edate = datetime.datetime.strptime("%s %s" % (end, year), "%B %d %Y")
                timestamp = o.attrs[0][1]
                yield FormRequest.from_response(response,
                            formname='accountActivityForm',
                        formdata={'statementTimePeriod': timestamp},
                        meta={'sd': sdate, 'ed': edate},
                        callback=self.parse_charges_page)

    def parse_charges_page(self, response):
        meta = response.request.meta
        start_date = meta['sd']
        end_date = meta['ed']

        if start_date in self.invoices:
            self.log("Skipping invoice as already in base %s" % start_date)
            return

        items = self._parse_charges(response.body)
        for item in items:
            item['startdate'] = start_date
            item['enddate'] = end_date
            item['usage'] = []
            if item['link']:
                yield Request(url=item['link'],
                    meta={'item': item},
                    callback=self.get_report)
                continue
            yield item

