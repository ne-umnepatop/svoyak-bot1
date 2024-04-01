import asyncio
import config
import datetime
from models import *
from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from db_api import DBAPI


class ExcursionDataState(StatesGroup):
    waiting_for_excursion_data = State()


db_api = DBAPI()
loop = asyncio.get_event_loop()
bot = Bot(config.PSIVD, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, loop, storage=storage)


@dp.message_handler(commands="start")
async def start_handler(message: types.Message, state: FSMContext):
    if Student.get_or_none(Student.tg_id == message.from_user.id) is not None:
        if message.from_user.id in config.ADMIN_IDS:
            callback_query = types.CallbackQuery(
                id="",
                from_user=message.from_user,
                chat_instance=message.chat.id,
                message=message,
                data="menu_prepod"
            )
            await menu_prepod(callback_query, state)
        else:
            callback_query = types.CallbackQuery(
                id="",
                from_user=message.from_user,
                chat_instance=message.chat.id,
                message=message,
                data="menu_student"
            )
            await menu_student(callback_query, state)
    else:
        await message.answer("Введите ваш ИСУ ID:")
        await state.set_state("isu_id")


@dp.message_handler(state="isu_id")
async def process_isu_id(message: types.Message, state: FSMContext):
    try:
        isu_id = int(message.text)
    except ValueError:
        await message.answer("Неверный формат ИСУ ID. Введите числовое значение.")
        return
    await message.answer("Введите ваше имя:")
    await state.update_data(isu_id=isu_id)
    await state.set_state("name")


@dp.message_handler(state="name")
async def process_name(message: types.Message, state: FSMContext):
    name = message.text
    await message.answer("Введите вашу группу (если вы организатор, можете ввести что угодно):")
    await state.update_data(name=name)
    await state.set_state("group")


@dp.message_handler(state="group")
async def process_group(message: types.Message, state: FSMContext):
    group = message.text
    async with state.proxy() as data:
        isu_id = data.get("isu_id")
        name = data.get("name")
    success = db_api.create_student(isu_id=isu_id, name=name, tg_id=message.from_user.id, group=group)
    if success:
        await message.answer("Студент успешно создан.")
        if message.from_user.id in config.ADMIN_IDS:
            await message.answer("Вы являетесь преподавателем.")
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="Я преподаватель", callback_data="menu_prepod"))
            await message.answer("Подтвердите свой статус:", reply_markup=keyboard)
        else:
            callback_query = types.CallbackQuery(
                id="",
                from_user=message.from_user,
                chat_instance=message.chat.id,
                message=message,
                data="menu_student"
            )
            await menu_student(callback_query, state)
    else:
        await message.answer("Ошибка при создании студента.")
    await state.finish()


@dp.callback_query_handler(text="menu_student")
async def menu_student(call: types.CallbackQuery, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(text="Записаться на экскурсии", callback_data="sign_in"),
        types.InlineKeyboardButton(text="Отписаться от экскурсии", callback_data="sign_out"),
        types.InlineKeyboardButton(text="Статистика", callback_data="stats")
    )
    await bot.send_message(
        chat_id=call.message.chat.id,
        text="🗺️ Главное меню 🗺️",
        reply_markup=keyboard
    )


@dp.callback_query_handler(text="menu_prepod")
async def menu_prepod(call: types.CallbackQuery, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(text="Отметить посещения", callback_data="mark"),
        types.InlineKeyboardButton(text="Добавить экскурсию", callback_data="add_excursion"),
        types.InlineKeyboardButton(text="Удалить экскурсию", callback_data="remove_excursion")
    )
    await bot.send_message(
        chat_id=call.message.chat.id,
        text="🗺️ Главное меню 🗺️",
        reply_markup=keyboard
    )


@dp.callback_query_handler(text="sign_in")
async def sign_in(call: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(call.id)

    excursions = db_api.get_available_excursions_for_student(call.from_user.id)
    if excursions:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for excursion in excursions:
            keyboard.add(types.InlineKeyboardButton(text=f"{excursion.name}: {excursion.datetime}",
                                                    callback_data=f"signin_{excursion.id}"))
        if len(keyboard.inline_keyboard) == 0:
            await bot.send_message(chat_id=call.message.chat.id,
                                   text="Извините, нет доступных экскурсий в данный момент.")
            await menu_student(call, state)
        else:
            await bot.send_message(chat_id=call.message.chat.id,
                                   text="Выберите экскурсию, на которую вы хотите записаться:")
            await bot.send_message(chat_id=call.message.chat.id, text="Доступные экскурсии:", reply_markup=keyboard)
    else:
        await bot.send_message(chat_id=call.message.chat.id, text="Извините, нет доступных экскурсий в данный момент.")
        await menu_student(call, state)


@dp.callback_query_handler(lambda call: call.data.startswith("signin_"))
async def excursion(call: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(call.id)
    excursion_id = int(call.data.split("_")[1])
    excursion = db_api.get_excursion(excursion_id)
    if excursion:
        db_api.signup_for_excursion(call.from_user.id, excursion_id)
        await bot.send_message(chat_id=call.message.chat.id, text=f"Вы записались на экскурсию {excursion.name}!")
    else:
        await bot.send_message(chat_id=call.message.chat.id, text="Извините, такой экскурсии не существует.")
    await menu_student(call, state)


@dp.callback_query_handler(text="sign_out")
async def sign_out(call: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(call.id)
    student_id = call.from_user.id
    excursions = db_api.get_student_excursions(student_id)

    if excursions:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for excursion in excursions:
            keyboard.add(types.InlineKeyboardButton(text=excursion.name, callback_data=f"cancel_{excursion.id}"))

        await bot.send_message(chat_id=call.message.chat.id, text="Выберите экскурсию для отписки:",
                               reply_markup=keyboard)
    else:
        await bot.send_message(chat_id=call.message.chat.id, text="Вы не записаны ни на одну экскурсию.")
        await menu_student(call, state)


@dp.callback_query_handler(lambda call: call.data.startswith("cancel_"))
async def cancel(call: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(call.id)
    excursion_id = int(call.data.split("_")[1])
    excursion = db_api.get_excursion(excursion_id)
    if excursion:
        if db_api.unsign_from_excursion(call.from_user.id, excursion_id):
            await bot.send_message(chat_id=call.message.chat.id, text=f"Вы отписались от экскурсии {excursion.name}.")
        else:
            await bot.send_message(chat_id=call.message.chat.id, text=f"Вы не можете отписаться от этой экскурсии.")
    else:
        await bot.send_message(chat_id=call.message.chat.id, text="Извините, такой экскурсии не существует.")
    await menu_student(call, state)


@dp.callback_query_handler(text="stats")
async def stats(call: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(call.id)
    msg = "Ваши посещённые экскурсии:\n"

    stats = db_api.get_user_stats(call.from_user.id)
    msg += "\n".join([f"{sign.excursion.datetime}: {sign.excursion.name}" for sign in stats])
    if not msg:
        msg = "Вы ещё не посетили ни на одну экскурсию."
    await bot.send_message(chat_id=call.message.chat.id, text=msg)


@dp.callback_query_handler(text="mark")
async def mark_students(call: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(call.id)

    excursions = db_api.get_excursions()
    if not excursions:
        await bot.send_message(chat_id=call.message.chat.id, text="Нет доступных экскурсий.")
        await menu_prepod(call, state)
    else:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for excursion in excursions:
            keyboard.add(types.InlineKeyboardButton(text=excursion.name, callback_data=f"mark_{excursion.id}"))

        await bot.send_message(chat_id=call.message.chat.id, text="Выберите экскурсию для отметки посещений:",
                               reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('mark_') and c.data.count('_') == 1)
async def process_callback_excursion(callback_query: types.CallbackQuery):
    excursion_id = int(callback_query.data.split('_')[1])
    excursion = db_api.get_excursion(excursion_id)
    signups = db_api.get_excursion_signups(excursion_id)
    if not signups:
        await bot.send_message(callback_query.from_user.id, f"Нет студентов, записанных на экскурсию")
        await menu_prepod(callback_query, None)
        return
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for sign in signups:
        keyboard.add(
            types.InlineKeyboardButton(text=sign.student.name, callback_data=f"mark_{excursion_id}_{sign.student.id}"))
    await bot.send_message(callback_query.from_user.id, f"Выберите студентов, посетивших экскурсию",
                           reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('mark_') and c.data.count('_') == 2)
async def process_callback_student(callback_query: types.CallbackQuery):
    excursion_id = int(callback_query.data.split('_')[1])
    student_id = int(callback_query.data.split('_')[2])
    excursion = db_api.get_excursion(excursion_id)
    student = db_api.get_student(student_id)
    db_api.mark_student_attendance(student.tg_id, excursion.id)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton(text="Завершить", callback_data=f"end_marking"))
    await bot.send_message(callback_query.from_user.id,
                           f"Студент {student.name} отмечен как посетивший экскурсию {excursion.name}",
                           reply_markup=keyboard)


@dp.callback_query_handler(text="end_marking")
async def end_marking(call: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(call.id)
    await bot.send_message(chat_id=call.message.chat.id, text="Отметка посещений завершена.")
    await menu_prepod(call, state)


@dp.callback_query_handler(text="add_excursion")
async def add_excursion(call: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(call.id)
    await bot.send_message(chat_id=call.message.chat.id,
                           text="Введите данные для добавления новой экскурсии:\nФормат ввода: 2023-06-20 14:00,Excursion Name,50,Excursion Place")
    await ExcursionDataState.waiting_for_excursion_data.set()


@dp.message_handler(state=ExcursionDataState.waiting_for_excursion_data)
async def process_excursion_data(message: types.Message, state: FSMContext):
    excursion_data = message.text.split(',')
    if len(excursion_data) != 4:
        await bot.send_message(chat_id=message.chat.id, text="Неверный формат данных для экскурсии.")
        return

    try:
        excursion_date = datetime.datetime.strptime(excursion_data[0], '%Y-%m-%d %H:%M')
        name = excursion_data[1].strip()
        people_limit = int(excursion_data[2])
        place = excursion_data[3].strip()
    except ValueError:
        await bot.send_message(chat_id=message.chat.id, text="Ошибка при обработке данных экскурсии.")
        return

    success = db_api.create_excursion(excursion_date, name, people_limit, place)
    if success:
        await bot.send_message(chat_id=message.chat.id, text="Экскурсия успешно добавлена.")
    else:
        await bot.send_message(chat_id=message.chat.id, text="Ошибка при добавлении экскурсии.")
    callback_query = types.CallbackQuery(
        id="",
        from_user=message.from_user,
        chat_instance=message.chat.id,
        message=message,
        data="menu_prepod"
    )
    await menu_prepod(callback_query, state)
    await state.finish()


@dp.callback_query_handler(text="remove_excursion")
async def remove_excursion(call: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(call.id)

    # Retrieve excursions from the database
    excursions = db_api.get_excursions()

    if excursions:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for excursion in excursions:
            keyboard.add(types.InlineKeyboardButton(text=excursion.name, callback_data=f"remove_{excursion.id}"))

        await bot.send_message(chat_id=call.message.chat.id, text="Выберите экскурсию для удаления:",
                               reply_markup=keyboard)
    else:
        await bot.send_message(chat_id=call.message.chat.id, text="Нет доступных экскурсий для удаления.")


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('remove_'))
async def process_callback_remove_excursion(callback_query: types.CallbackQuery):
    excursion_id = int(callback_query.data.split('_')[1])
    excursion = db_api.get_excursion(excursion_id)
    db_api.remove_excursion(excursion_id)
    await bot.send_message(callback_query.from_user.id, f"Экскурсия {excursion.name} удалена")
    await menu_prepod(callback_query, None)


if __name__ == '__main__':
    executor.start_polling(dp)
