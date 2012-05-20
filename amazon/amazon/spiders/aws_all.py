import datetime
import calendar
from BeautifulSoup import BeautifulSoup

from scrapy.http import Request, FormRequest

from amazon.items import AmazonCharges
from aws import AwsSpiderBase

class AwsSpiderAll(AwsSpiderBase):
    name = 'aws_hist'

    def parse_aws(self, response):
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
        items = self._parse_charges(response.body)
        meta = response.request.meta
        start_date = meta['sd']
        end_date = meta['ed']
        for item in items:
            if dict(cloud_account_id=self.user_id, service=item['service'], startdate=start_date, enddate=end_date) in self.invoices:
                self.log.msg("Skipping invoice as already in base %s" % item)
                continue
            item['startdate'] = start_date
            item['enddate'] = end_date
            if item['link']:
                yield Request(url=item['link'],
                    meta={'date_from': start_date, 'date_to': end_date},
                    callback=self.get_report)
            yield item



