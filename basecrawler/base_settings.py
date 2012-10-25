
USER_AGENT = '''Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.162 Safari/535.19'''
USER_ID = None
KEY = 'yDo4V5B0j9V3JRJ4lO55q77Wm5r7dLC8'

MONGO_DB = 'xervmon_remote'
MONGO_USER = 'xervmon_remote'
MONGO_PASSWORD = 'xervmonremote'
MONGO_PORT = '27017'
MONGO_IP = '184.106.197.102'
MONGO_HOST = 'mongodb://%s:%s@%s:%s/%s' % (MONGO_USER, MONGO_PASSWORD, MONGO_IP,
                             MONGO_PORT, MONGO_DB)

MYSQL_USER = 'xervmon_remote'
MYSQL_PASSWORD = 'Java23man'
MYSQL_DB = 'controlpanel'
MYSQL_HOST = '184.106.197.102'

USER_ID = None
KEY = 'yDo4V5B0j9V3JRJ4lO55q77Wm5r7dLC8'
CAPTCHA_KEY = '4fe73c77a83c95a2c6fe146c509dfe88'

SENDER_EMAIL = 'sysadmin@hooduku.com'
SENDER_PASSWORD = 'admin9873%man'
RECEIVER_EMAIL = 'sudhi@hooduku.com'
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = '587'
MONGO_LOG = 'scrape_log'

XWEBSERVICE_HOST = 'crawler.xervmon.com'
XWEBSERVICE_PORT = 5000
XWEBSERVICE_USER = 'xervmon'
XWEBSERVICE_PASSWD = 'xervmon_pass'
XWEBSERVICE_PREDICT = True

SPIDER_MIDDLEWARES = {
        'basecrawler.middlewares.ErrorsMiddleware': 100
        }

DOWNLOADER_MIDDLEWARES = {
        'basecrawler.middlewares.ErrorDownloader': 100
        }
EXTENSIONS = {
	'scrapy.contrib.feedexport.FeedExporter': None,
        'basecrawler.extensions.FailLogger': 599,
        'basecrawler.extensions.XWebservice': 598
        }
