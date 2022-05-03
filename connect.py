import pymysql
from config import *

db = pymysql.connect(
    user=user,
    password=password,
    host=host,
    database=database,
    autocommit=autocommit
)
cursor = db.cursor()