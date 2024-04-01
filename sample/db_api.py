import random
import datetime
from models import *


class DBAPI(object):
    def __init__(self):
        db.connect()
        db.create_tables([Student, Excursion, ExcursionSignup])

    def verify_excursion_signs(self, excursion_id: int):
        signed_students = self.get_excursion_signups(excursion_id)
        excursion = self.get_excursion(excursion_id)
        people_count_goal = excursion.people_limit
        if people_count_goal is None or people_count_goal == 0 or people_count_goal > len(signed_students):
            for signup in signed_students:
                signup.is_verified = True
                signup.save()
        else:
            for i in range(1, 6):
                for signup in signed_students:
                    if signup.student.priority != i:
                        continue
                    signup.is_verified = True
                    signup.save()
                    people_count_goal -= 1
                    if people_count_goal == 0:
                        return

    def create_student(self, isu_id: int, name: str, tg_id: int, group: str, is_staff: bool = False,
                       probability: float = 1.0) -> bool:
        """
        Creates a user with given parameters
        """
        if Student.get_or_none(Student.tg_id == tg_id) is not None:
            return False
        Student.create(isu_id=isu_id, name=name, tg_id=tg_id, group=group, is_staff=is_staff,
                       probability=probability).save()
        return True

    def get_student(self, tg_id: int) -> Student:
        return Student.get(Student.tg_id == tg_id)

    def create_excursion(self, datetime: datetime.datetime, name: str, people_limit=0, place='', priority='') -> bool:
        """
        Creates an excursion with given parameters
        """
        if Excursion.get_or_none(Excursion.datetime == datetime and Excursion.name == name) is not None:
            return False
        Excursion.create(datetime=datetime, name=name, people_limit=people_limit, place=place,
                         priority=priority)
        return True

    def get_excursions(self) -> list[Excursion]:
        """
        Retrieves the available excursions from the database
        """
        return Excursion.select().execute()

    def get_excursion(self, excursion_id: int) -> Excursion:
        return Excursion.get(Excursion.id == excursion_id)

    def remove_excursion(self, excursion_id: int) -> None:
        excursion = Excursion.get(Excursion.id == excursion_id)
        for signup in ExcursionSignup.select().where(ExcursionSignup.excursion == excursion).execute():
            signup.delete_instance()
        excursion.delete_instance()

    def get_student_excursions(self, tg_id: int):
        """
        Returns a list of excursions which student is signed for
        """
        student = Student.get(Student.tg_id == tg_id)
        return Excursion.select().join(ExcursionSignup).where(ExcursionSignup.student == student).execute()

    def get_excursion_signups(self, excursion_id: int):
        """
        Returns a list of students signed for the excursion
        """
        excursion = Excursion.get(Excursion.id == excursion_id)
        return ExcursionSignup.select().where(ExcursionSignup.excursion == excursion)

    def signup_for_excursion(self, tg_id: int, excursion_id: int):
        """
        Returns True if signup was successful, False otherwise
        """
        student = Student.get(Student.tg_id == tg_id)
        excursion = Excursion.get(Excursion.id == excursion_id)
        if excursion.people_limit is not None and excursion.currently_signed >= excursion.people_limit:
            return False
        ExcursionSignup.create(student=student, excursion=excursion).save()
        if excursion.people_limit is not None:
            excursion.currently_signed += 1
            excursion.save()
        return True

    def unsign_from_excursion(self, tg_id: int, excursion_id: int) -> None:
        """
        Returns True if unsign was successful, False otherwise
        """
        student = Student.get(Student.tg_id == tg_id)
        excursion = Excursion.get(Excursion.id == excursion_id)
        signup = ExcursionSignup.get(ExcursionSignup.student == student, ExcursionSignup.excursion == excursion)
        if signup.attended or datetime.datetime.now() > excursion.datetime:
            return False
        signup.delete_instance()
        return True

    def mark_student_attendance(self, tg_id: int, excursion_id: int):
        """
        Mark student attendance at the excursion
        """
        student = Student.get(Student.tg_id == tg_id)
        excursion = Excursion.get(Excursion.id == excursion_id)
        signup = ExcursionSignup.get(ExcursionSignup.student == student, ExcursionSignup.excursion == excursion)
        signup.attended = True
        signup.save()

    def get_available_excursions(self) -> list[Excursion]:
        """
        Returns a list of now available excursions
        """
        return Excursion.select().where(
            Excursion.datetime > datetime.datetime.now() + datetime.timedelta(seconds=30) and
            Excursion.currently_signed < Excursion.people_limit).execute()

    def get_available_excursions_for_student(self, tg_id: int) -> list[Excursion]:
        """
        Returns a list of now available excursions for the student
        """
        student = Student.get(Student.tg_id == tg_id)
        student_signups = ExcursionSignup.select().where(ExcursionSignup.student == student).execute()
        signed_excursions = []
        for signup in student_signups:
            signed_excursions.append(signup.excursion.id)
        return Excursion.select().where(
            Excursion.datetime > datetime.datetime.now() + datetime.timedelta(seconds=30) and
            Excursion.currently_signed < Excursion.people_limit and Excursion.id not in signed_excursions).execute()

    def get_user_stats(self, tg_id: int) -> list[Excursion]:
        """
        Returns a dictionary of user statistics
        """
        student = Student.get(Student.tg_id == tg_id)
        return ExcursionSignup.select().where(
            ExcursionSignup.student == student and ExcursionSignup.attended == True).execute()
