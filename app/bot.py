from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ChatType
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import TelegramConfig
from app.routers import admin_router, user_router
from app.routers.users.admin import db


cfg = TelegramConfig()

bot = Bot(token=cfg.token.get_secret_value())
dp = Dispatcher()
dp.include_routers(admin_router, user_router)

storage = MemoryStorage()


async def main():
    await db.connect()
    await db.initialize()
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
