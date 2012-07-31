import datetime
import calendar

from scrapy.http import Request

from amazon.items import AmazonCharges
from aws import AwsSpiderBase

class AwsSpiderCurrent(AwsSpiderBase):
    name = 'aws_current'

    def parse_aws(self, response):
        if not self.check_permission(response):
            return
            

        self.log.msg("started to parse items for %s" % self.name)
        now = datetime.datetime.now()
        dater = calendar.monthrange(now.year, now.month)
        start_date = datetime.datetime.strptime("%d-%d-1" % (now.year, now.month), '%Y-%m-%d')
        end_date = datetime.datetime.strptime("%d-%d-%d" % (now.year, now.month, dater[1]), '%Y-%m-%d')
        items = self._parse_charges(response.body)
        self.log.msg("Items %s" % str(items))
        for item in items:
            item['startdate'] = start_date
            item['enddate'] = end_date
            if item['link']:
                yield Request(url=item['link'],
                    meta={'date_from': start_date, 'date_to': end_date},
                    callback=self.get_report)
            yield item


