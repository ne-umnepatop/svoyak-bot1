from peewee import *

db = SqliteDatabase('data.db')


class BaseModel(Model):
    class Meta:
        database = db


class Student(BaseModel):
    isu_id = IntegerField(primary_key=True)
    name = CharField()
    tg_id = IntegerField()
    group = CharField(null=True)
    is_staff = BooleanField(default=False)
    priority = IntegerField(default=5)


class Excursion(BaseModel):
    id = IntegerField(primary_key=True)
    datetime = DateTimeField()
    name = CharField()
    people_limit = IntegerField(null=True)
    currently_signed = IntegerField(default=0)
    place = CharField(default='')


class ExcursionSignup(BaseModel):
    student = ForeignKeyField(Student)
    excursion = ForeignKeyField(Excursion)
    is_verified = BooleanField(default=False)
    attended = BooleanField(default=False)
