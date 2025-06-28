from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ChatType
from aiogram.fsm.storage.memory import MemoryStorage

from SpotifyBot.app.config import TelegramConfig
from SpotifyBot.app.routers import admin_router, user_router
from SpotifyBot.app.routers.users.admin import db

cfg = TelegramConfig()

bot = Bot(token=cfg.token.get_secret_value())
dp = Dispatcher()
dp.include_routers(admin_router, user_router)

storage = MemoryStorage()


@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    if message.chat.type == ChatType.GROUP:
        await message.reply("Spotify bot in the spot!")
    else:
        await message.reply("Spotify bot here!")

async def main():
    await db.connect()
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
