from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ChatType
from aiogram.utils.keyboard import InlineKeyboardBuilder

from SpotifyBot.app.db import Database
from SpotifyBot.app.config import TelegramConfig
from SpotifyBot.app.functions import (load_config,
                                      save_config,
                                      logger)


cfg = TelegramConfig()
bot = Bot(token=cfg.token.get_secret_value())
dp = Dispatcher()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.reply("Spotify bot here!")


@dp.message(Command("update"))
async def update_cmd(message: types.Message):
    if (message.chat.type != ChatType.PRIVATE and
        message.from_user.id == cfg.admin_id):
        return # Only process DMs from admin

    parts = message.text.split(maxsplit=3)
    config = load_config()
    if  not 2 < len(parts) < 5:
        return await message.answer(
            '\n'.join(f"{k}: {v}" for k, v in config.items()) + '\n\n'
            + "Usage: /update <KEY> <VALUE> <add/delete>\n"
            + "NOTE: <add/delete> does not work for price!"
        )

    key, value = parts[1], parts[2]
    if key == "price":
        try:
            config[key] = int(value)
            save_config(config)
            await message.answer(f"Updated {key} on {value} successfully!")
        except Exception as e:
            await message.answer(f"Error updating {key}: {e}")
    elif key == "bank_accounts":
        try:
            action = parts[3]
        except IndexError:
            await message.answer("Please, complete your query with 'add' or 'delete'.")
            return
        if action == "add":
            try:
                config[key].append(value)
                save_config(config)
                await message.answer(f"Added {key} on {value} successfully!")
            except Exception as e:
                await message.answer(f"Error adding {key}: {e}")
        elif action == "delete":
            try:
                config[key].remove(value)
                save_config(config)
                await message.answer(f"Deleted {value} from {key} successfully!")
            except Exception as e:
                await message.answer(f"Error deleting {key}: {e}")
        else:
            await message.reply("There is no such action! Please, complete your query with 'add' or 'delete'.")
    else:
        await message.reply("There is no such key! Please, choose from provided list.")


@dp.message(Command("link"))
async def link_user(message: types.Message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return  # Only process GMs (groups)

    user_id = message.from_user.id
    group_id = message.chat.id


@dp.message(Command("delete"))
async def link_user(message: types.Message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return  # Only process GMs (groups)

    user_id = message.from_user.id
    group_id = message.chat.id


@dp.message(Command("pay"))
async def pay_bill(message: types.Message):
    if message.chat.type != ChatType.PRIVATE:
        return  # Only process DMs

    # Create inline keyboard with month options
    builder = InlineKeyboardBuilder()
    for i in range(1, 7):
        builder.button(text=str(i), callback_data=f"month_{i}")
    builder.adjust(3)

    await message.answer(
        text="For how many months do you want to pay?",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("month_"))
async def handle_month_choice(callback: types.CallbackQuery):
    month = callback.data.split("_")[1]
    await callback.message.answer(f"You chose {month} month{'s' if month != '1' else ''}!")
    await callback.answer()


@dp.message()
async def handle_pdf(message: types.Message):
    if message.chat.type != ChatType.PRIVATE:
        return  # Only process DMs
    """
    if message.document and message.document.mime_type == 'application/pdf':
        user_id = message.from_user.id
        group_id = await get_user_group(user_id)
        if group_id:
            await mark_payment(user_id, group_id)
            await message.reply("✅ PDF received and your payment has been recorded.")
        else:
            await message.reply("❌ You are not linked to any group. Please contact the admin.")
    """
    print(message.from_user.id)
    print(message.chat.id)
    print(type(message.from_user.id))

    await message.reply("❌ You are not linked to any group. Please contact the admin.")


async def main():
    # await init_db()
    # setup_scheduler(bot)
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
