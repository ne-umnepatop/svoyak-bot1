import datetime
import logging
from models import *
from db_api import DBAPI

logger = logging.getLogger('peewee')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

db = DBAPI()
db.create_student(123, "Test", 1234, "TestGR")
student = Student.get()
print(student)
db.create_excursion(datetime.datetime.now() + datetime.timedelta(days=1), "Excursion 1", True, 2)
db.create_excursion(datetime.datetime.now() + datetime.timedelta(days=2), "Excursion 2", True, 2)
exc: Excursion = db.get_available_excursions()
print(exc)
