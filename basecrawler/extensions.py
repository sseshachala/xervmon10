import urllib2
from urlparse import urljoin

from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher

class FailLogger(object):
    def __init__(self):
        dispatcher.connect(self.spider_error, signal=signals.spider_error)

    def spider_error(self, failure, response, spider):
        spider.errors.append(failure.getTraceback())
                

class XWebservice(object):
    def __init__(self, host, port, user, password, user_id):
        self.host = host
        self.port = port
        self.user = user
        self.user_id = user_id
        self.password = password
        self.url_base = self.get_url_string()


    def get_url_string(self):
        if not self.host:
            return None
        url = 'http://%s' % self.host
        if self.port:
            url = '%s:%s' % (url, self.port)
        return url

    @classmethod
    def from_crawler(cls, crawler):
        is_run_predict = crawler.settings.getbool('XWEBSERVICE_PREDICT')
        host = crawler.settings.get('XWEBSERVICE_HOST')
        port = crawler.settings.get('XWEBSERVICE_PORT')
        user = crawler.settings.get('XWEBSERVICE_USER')
        user_id = crawler.settings.get('USER_ID')
        password = crawler.settings.get('XWEBSERVICE_PASSWD')
        ext = cls(host, port, user, password, user_id)

        if is_run_predict:
            dispatcher.connect(ext.run_predict, signal=signals.spider_closed)
        return ext

    def open_url(self, url_part):
        url = urljoin(self.url_base, url_part)
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url, self.user, self.password)
        auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(auth_handler)
        resp = opener.open(url)
        return resp.read()

    def run_predict(self, spider):
        spider.log("Closed signal got")
        user_id = self.user_id
        url = '/predict/start/%s/' % user_id
        self.open_url(url)

