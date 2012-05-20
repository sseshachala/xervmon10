
database_user="xervmon_remote"
database_password="Java23man"
database_name = "controlpanel"
database_host = "184.106.197.102"

update_hours = 12

mongo_host = "184.106.197.102"
mongo_port = 27017
mongo_dbname = "xervmon_remote"
mongo_user = "xervmon_remote"
mongo_password = "xervmonremote"

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

if database_password == "":
    connect_str = 'mysql+mysqldb://%s@%s/%s' % (database_user, database_host, database_name)
else:
    connect_str = 'mysql+mysqldb://%s:%s@%s/%s' % (database_user, database_password, database_host, database_name)
engine = create_engine(connect_str, echo=False)
SqliteSession = sessionmaker(bind=engine)
session = SqliteSession()
Base.metadata.bind = engine
