import datetime
import random
import time
import sqlite3
import pandas as pd

now = datetime.datetime.now()
date_str = now.strftime('%Y-%m-%d %H:%M:%S')
# stud_tbl, org_tbl, excursions, attendees, zapys, pot_zapys = [], [], [], [], [], []
stud_tbl, org_tbl, excursions, attendees, zapys, pot_zapys = {}, {}, [], [], [], []
main_db = 'VPD_Excurs.db'
conn = sqlite3.connect(main_db)
cursor = conn.cursor()
# таблица Stud_tbl(id, name, tg_id) студентов с табельным, ФИО, номером из тг
create_students_table = '''
CREATE TABLE IF NOT EXISTS Stud_tbl (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  tg_id INTEGER,
  grup TEXT);'''
# таблица Excursions(date_time, name, place) экскурсий со временем, названием, местом
create_excursions_table = '''
CREATE TABLE IF NOT EXISTS Excursions (
  date_time TEXT,
  name TEXT NOT NULL,
  place TEXT NOT NULL,
  priority TEXT,
  [limit] INTEGER,
  PRIMARY KEY (date_time, name));'''
# таблица Attendees(id,excursion_date_time) совершённых посещений с табельным и датой, временем посещения
create_attendees_table = '''
CREATE TABLE IF NOT EXISTS Attendees (
  id INTEGER REFERENCES Stud_tbl(id),
  excursion_date_time TEXT NOT NULL REFERENCES Excursions(date_time),
  PRIMARY KEY (id, excursion_date_time)
);'''
# таблица Pot_zapys(id,excursion_date_time, click_time) потенциальных посещений с табельным и датой, временем посещенияи нажатия для участия в рандоме
create_potential_zapys_table = '''
CREATE TABLE IF NOT EXISTS Pot_zapys (
  id INTEGER REFERENCES Stud_tbl(id),
  excursion_date_time TEXT NOT NULL REFERENCES Excursions(date_time),
  click_time INTEGER,
  PRIMARY KEY (id, excursion_date_time)
);'''
# таблица Zapys(id,excursion_date_time) одобренных с табельным и датой, временем посещения
create_zapys_table = '''
CREATE TABLE IF NOT EXISTS Zapys (
  id INTEGER REFERENCES Stud_tbl(id),
  excursion_date_time TEXT NOT NULL REFERENCES Excursions(date_time),
  PRIMARY KEY (id, excursion_date_time)
);'''
# таблица Org_tbl(id, name, tg_id) организаторов с табельным, ФИО, номером из тг
create_orgs_table = '''
CREATE TABLE IF NOT EXISTS Org_tbl (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  tg_id INTEGER);'''
cursor.execute(create_students_table)
cursor.execute(create_excursions_table)
cursor.execute(create_attendees_table)
cursor.execute(create_orgs_table)
cursor.execute(create_zapys_table)
cursor.execute(create_potential_zapys_table)
conn.commit()
# только что было проверено наличие таблиц данных


class Man:
    """Cущность человека c int табельный, str ФИО, int номер из телеги"""
    classname = 'Человек'
    objcnt = 0

    def __init__(self, id, name, telegram_id):
        """На вход int табельный, str ФИО, int номер из телеги, добавляет сущность человека"""
        self.id = int(id)  # Табельное
        self.name = name  # ФИО
        self.tg_id = telegram_id
        Man.objcnt += 1

    def __repr__(self):
        return f'{self.id}'


class Student(Man):
    classname = 'Студент'
    """Чувак, который имеет табельный, ФИО, номер из тг
    С ним можно 
    .stat для вывода статистики
    .zapys для записи на экскурсию
    .otpys для удаления из списка записанных
    .posetil от лица организатора для отметки посещаемости"""

    def __init__(self, id, name, telegram_id, group):
        super().__init__(id, name, telegram_id)
        self.group = group
        cursor.execute("SELECT * FROM Stud_tbl WHERE id=?", (id,))
        result = cursor.fetchone()
        if not result:
            cursor.execute("INSERT INTO Stud_tbl (id, name, tg_id, grup) VALUES (?, ?, ?, ?)",
                           (id, name, telegram_id, group))
            conn.commit()
            # print("Запись успешно добавлена")
        # else:
        #     print('Уже существует')

    def stat(self):
        """Функция как будто не доделана, на вход ничего, на выход то, что посетил и то, на что записан"""
        requested = cursor.execute(
            "SELECT excursion_date_time, name FROM Excursions, Attendees WHERE id=? and excursion_date_time=date_time",
            (self.id,))
        return requested
        # будет запрос к SQL, чтобы вывести, что уже посетил, и что не посетил и дата > текущей

    def zapys(self, date_time):
        """На вход дата-время в формате SQLite, добавит запись в потенциальные"""
        cursor.execute("SELECT * FROM Pot_zapys WHERE id=?", (self.id,))
        try:
            if not cursor.fetchone():
                cursor.execute("INSERT INTO Pot_zapys (id, excursion_date_time, click_time) VALUES (?, ?, date_str)",
                               (self.id, date_time))
                conn.commit()
                pot_zapys.append([self.id, date_time, time.time()])
                return f"Запись успешно добавлена"
            else:
                return f'Вы уже были записаны'
        except:
            return f'Не вышло'

    def otpys(self, date_time):
        """На вход дата-время в формате SQLite, удалит из потенциальных"""
        try:
            cursor.execute("DELETE FROM Pot_zapys WHERE id = ? "
                           "AND excursion_date_time = ?;",
                           (self.id, date_time))
            conn.commit()
            return f'Успешно'
        except:
            return f'Не вышло'

    def posetil(self, date_time):
        """На вход дата-время в формате SQLite, добавит запись в посещённые"""
        cursor.execute("SELECT * FROM Attendees WHERE id=?", (self.id,))
        try:
            if not cursor.fetchone():
                cursor.execute("INSERT INTO Attendees (id, excursion_date_time) VALUES (?, ?)", (self.id, date_time))
                conn.commit()
                attendees.append([self.id, date_time])
                return f"Запись успешно добавлена"
            else:
                return f'Уже был отмечен'
        except:
            return f'Не вышло'

    def notify(self, date):
        """Должна уведомлять, но пока только формирует строку уведомления
        И ВЫВОДИТ ЕЁ НА ЭКРАН"""
        cursor.execute("SELECT name FROM Excursions WHERE date_time =?", (date,))
        name = cursor.fetchone()[0]
        f = f'Вы ({self.name}) были автоматически записаны на {name} в {date}'
        print(f)  # УБРАТЬ КАК ТОЛЬКО ПРИДУМАЕМ УВЕДОМЛЕНИЯ
        return f


class Organizer(Man):
    classname = 'Организатор'

    def __init__(self, id, name, telegram_id):
        super().__init__(id, name, telegram_id)
        cursor.execute("SELECT * FROM Org_tbl WHERE id=?", (id,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Org_tbl (id,name, tg_id) VALUES (?, ?, ?)", (id, name, telegram_id))
            print("Запись успешно добавлена")
        # else:
        #     print('Уже существует')
        conn.commit()


class Excursion:
    classname = 'Экскурсия'

    def __init__(self, date_time, name, place, priority, limit):
        self.date_time = date_time
        self.name = name
        self.place = place
        self.priority = priority
        self.limit = limit
        cursor.execute("SELECT * FROM Excursions WHERE date_time=? and name=?", (date_time, name))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Excursions (date_time, name, place, priority, [limit]) VALUES (?, ?, ?, ?, ?)",
                           (date_time, name, place, priority, limit))
            conn.commit()
            print("Запись успешно добавлена")
        # else:
        #     print('Уже существует')

    def __repr__(self):
        return f'В {self.date_time} будет {self.name} по адресу {self.place}'


# восстанавливаем данные
def restore():
    cursor.execute("SELECT * FROM Stud_tbl")
    rows = cursor.fetchall()
    for row in rows:
        if not any(stud_tbl[student].id == row[0] for student in stud_tbl):
            student = Student(row[0], row[1], row[2], row[3])
            stud_tbl[row[0]] = student
    cursor.execute("SELECT * FROM Excursions")
    rows = cursor.fetchall()
    for row in rows:
        excursions.append(Excursion(row[0], row[1], row[2], row[3], row[4]))
    cursor.execute("SELECT * FROM Org_tbl")
    rows = cursor.fetchall()
    for row in rows:
        ogr = Organizer(row[0], row[1], row[2])
        org_tbl[row[0]] = ogr
    cursor.execute("SELECT * FROM Attendees")
    rows = cursor.fetchall()
    for row in rows:
        attendees.append((row[0], row[1]))
    cursor.execute("SELECT * FROM Zapys")
    rows = cursor.fetchall()
    for row in rows:
        zapys.append((row[0], row[1]))
    cursor.execute("SELECT * FROM Pot_zapys")
    rows = cursor.fetchall()
    for row in rows:
        pot_zapys.append((row[0], row[1]))
    print("Восстановлено")


# для всех действий можно пользоваться функциями hotfix, работающими напрямую с БД в обход сущностей
def hotfix_posetil(id, date_time):
    """Мало ли не выйдет иначе, наверное, лишний код
    На вход табельный и дата-время в формате SQLite, добавит запись в посещённые"""
    cursor.execute("SELECT * FROM Attendees WHERE id=?", (id,))
    try:
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Attendees (id, excursion_date_time) VALUES (?, ?)", (id, date_time))
            conn.commit()
            return f"Запись успешно добавлена"
        else:
            return f'Уже был отмечен'
    except:
        return f'Не вышло'


def hotfix_otpys(id, date_time):
    """Мало ли не выйдет иначе, наверное, лишний код
    На вход табельный и дата-время в формате SQLite, удалит из потенциальных"""
    try:
        cursor.execute("DELETE FROM Pot_zapys WHERE id = ? "
                       "AND excursion_date_time = ?;",
                       (id, date_time))
        conn.commit()
        return f'Успешно'
    except:
        return f'Не вышло'


def hotfix_zapys(id, date_time):
    """Мало ли не выйдет иначе, наверное, лишний код
    На вход табельный и дата-время в формате SQLite, добавит запись в потенциальные"""
    cursor.execute("SELECT * FROM Pot_zapys WHERE id=?", (id,))
    # try:
    if not cursor.fetchone():
        cursor.execute("INSERT INTO Pot_zapys (id, excursion_date_time, click_time) VALUES (?, ?, ?)",
                       (id, date_time, date_str))
        conn.commit()
        return f"Запись успешно добавлена"
    else:
        return f'Вы уже были записаны'
    # except:
    #     print('Не вышло')
    #     return f'Не вышло'


def hotfix_blat(id, date_time):
    """Мало ли не выйдет иначе, наверное, лишний код
    На вход табельный и дата-время в формате SQLite, добавит запись в выбранные.
    Использовать с осторожностью: если нет id среди студентов, ломает код"""
    cursor.execute("SELECT * FROM Zapys WHERE id=?", (id,))
    # try:
    if not cursor.fetchone():
        cursor.execute("INSERT INTO Zapys (id, excursion_date_time) VALUES (?, ?)",
                       (id, date_time))
        conn.commit()
        return f"Запись успешно добавлена"
    else:
        return f'Вы уже были записаны'
    # except:
    #     print('Не вышло')
    #     return f'Не вышло'


def random_pys(excursion_date_time):
    # Get all existing Zapys for this excursion from the database
    query = '''
           SELECT id
           FROM Zapys
           WHERE excursion_date_time = ?;
       '''
    cursor.execute(query, (excursion_date_time,))
    existing_zapys = set(r[0] for r in cursor.fetchall())

    # Get all Pot_zapys for this excursion from the database
    query = '''
           SELECT id, click_time 
           FROM Pot_zapys
           WHERE excursion_date_time = ?;
       '''
    cursor.execute(query, (excursion_date_time,))
    pot_zapys = cursor.fetchall()

    # Get limit from Excursions table
    query = '''
           SELECT [limit]
           FROM Excursions
           WHERE date_time = ?;
       '''
    cursor.execute(query, (excursion_date_time,))
    limit = cursor.fetchone()[0]

    # Calculate the probability of selecting each potential Zapys
    query = '''
           SELECT priority
           FROM Excursions
           WHERE date_time = ?;
       '''
    cursor.execute(query, (excursion_date_time,))
    priority = cursor.fetchone()[0]

    if priority == 'A':
        prob_ratio = 2
    else:
        prob_ratio = 1

    total_prob = sum(prob_ratio for _, _ in pot_zapys)
    selection_probs = [(id, prob_ratio / total_prob) for id, _ in pot_zapys]

    # Randomly select new Zapys and insert them into the Zapys table
    new_zapys = random.choices(selection_probs, k=limit - len(existing_zapys))
    for id, _ in new_zapys:
        if id not in existing_zapys:
            query = '''
                   INSERT OR REPLACE INTO Zapys (id, excursion_date_time)
                   VALUES (?, ?);
               '''
            cursor.execute(query, (id, excursion_date_time))
    conn.commit()
    cursor.execute("SELECT * FROM Zapys")
    rows = cursor.fetchall()
    for row in rows:
        stud_tbl[row[0]].notify(row[1])


def get_all_info():
    """Выводит все таблицы через data frame (pandas)"""
    print(f'Содержимое всех таблиц на данный момент:')
    tables = ['Stud_tbl', 'Excursions', 'Attendees', 'Pot_zapys', 'Zapys', 'Org_tbl']
    for table in tables:
        query = f"SELECT * FROM {table}"
        df = pd.read_sql_query(query, conn)
        print(f"{table}:")
        print(df)


def no_repeat(tbl):
    cursor.execute(f"DELETE FROM {tbl} WHERE rowid NOT IN (SELECT MIN(rowid) FROM {tbl} GROUP BY id)")
    conn.commit()


conn.commit()
restore()
if __name__ == '__main__':
    # Существуют люди
    stud_tbl[3682] = Student(3682, "Зелепугин Андрей Юрьевич", 793241, 'R3142')
    stud_tbl[3689] = Student(3689, "Хафизов Родион Андреевич", 793249, 'R3137')
    stud_tbl[3587] = Student(3587, "Кутузов Михаил Андреевич", 793241, 'R3140')
    for i in range(350, 3500):
        stud_tbl[i] = Student(i, "Безымянный болванчик", i, f'R{i // 10}')
        hotfix_zapys(i, "2023-06-13 16:00")
    org_tbl[368201] = Organizer(368201, "Зелепугин Андрей Юрьевич", 793241)
    # Создаем экскурсию
    excursions.append(Excursion("2023-06-13 16:00", "Вводный урок", "Кронверский 49", "Null", 120))
    random_pys("2023-06-13 16:00")
    # Симуляция того, что некоторые студенты пришли на экскурсию
    stud_tbl[3689].posetil('2023-06-14 01:06:56.506')
    # hotfix_blat(368201, "2023-06-13 16:00")
    get_all_info()
    conn.close()
