from aiogram import Router, types, F
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .users.user import User
from ..tools import ErrorLogger

user_router = Router()
user = User()

logger = ErrorLogger()


@user_router.message(Command("pay"))
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

@user_router.callback_query(F.data.startswith("month_"))
async def handle_month_choice(callback: types.CallbackQuery):
    month = callback.data.split("_")[1]
    await callback.message.answer(f"You chose {month} month{'s' if month != '1' else ''}!")
    await callback.answer()