from contextlib import suppress

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from motor.core import AgnosticDatabase as MDB
from pymongo.errors import DuplicateKeyError

from keyboards import reply_builder

router = Router()


@router.message(CommandStart())
async def start(message: Message, db: MDB) -> None:
    with suppress(DuplicateKeyError):
        await db.users.insert_one({
            "_id": message.from_user.id,
            "status": 0
        })

    await message.reply(
        "Начинай поиск собеседника!",
        reply_markup=reply_builder("☕ Искать собеседника")
    )