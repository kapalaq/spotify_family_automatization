from aiogram import Router, types
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime

from SpotifyBot.app.tools import LinkForm, SettingsForm, YAMLConfig
from SpotifyBot.app.tools import ErrorLogger
from .users.admin import Admin


admin_router = Router()
admin = Admin()
storage = MemoryStorage()

logger = ErrorLogger()


@admin_router.message(Command("unpaid"))
async def get_unpaid(message: types.Message):
    """Get all unpaid groups.

    This function returns all groups that
    contains at least one unpaid user.
    In accordance with inner logic of Database,
    an user is classified as unpaid if his payment
    deadline is behind current time.

    Args:
        message: a message from the admin.

    Returns:
        None, answer with appropriate response.
    """
    if (message.chat.type != ChatType.PRIVATE or
        not admin.is_admin(message.from_user.id)):
        return  # Only process DMs from admin

    response = await admin.get_unpaid_group()

    await message.answer(response)


@admin_router.message(Command("update"))
async def update_settings(message: types.Message,  state: FSMContext) -> None:
    """Process /update command from admin

    It will start dialogue that helps admin
    update subscription price.

    Args:
        message: a message from the admin.
        state: state object for dialogue.

    Returns:
        None, will send message according to the next dialogue step.
    """

    if (message.chat.type != ChatType.PRIVATE or
        not admin.is_admin(message.from_user.id)):
        return  # Only process DMs from admin

    await message.answer("Hey! What do you want to update?",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 [
                                     KeyboardButton(text="price"),
                                 ]
                             ],
                             resize_keyboard=True,
                         ))
    await state.set_state(SettingsForm.target)

@admin_router.message(SettingsForm.target)
async def process_target(message: types.Message, state: FSMContext) -> None:
    """Process target value from admin.

    This function make sure admin will enter
    target correctly with Telegram specific validation.

    Args:
        message: a message from the admin.
        state: state object for dialogue.

    Returns:
        None, will send message according to the next dialogue step.
    """

    target = message.text.strip().lower().replace(' ', '_')
    data = YAMLConfig().load_config()

    if target == 'price':
        await message.answer(
            f"""
            Please, provide me with payment value you want to be effective.
            Note: current price is {data['price']} KZT
            """,
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer(f"There are no settings named {target}. Please try again.")
        await state.set_state(SettingsForm.target)
        return

    await state.update_data(target=target)
    await state.set_state(SettingsForm.value)

@admin_router.message(SettingsForm.value)
async def process_value(message: types.Message, state: FSMContext) -> None:
    """Process update value from admin.

    This function make sure admin will enter
    value for update correctly with logic specific validation.

    Args:
        message: a message from the admin.
        state: state object for dialogue.

    Returns:
        None, will send message according to the next dialogue step.
    """

    value = int(message.text.strip())
    if value <= 0:
        await message.answer("Your value is less or equal to 0. Please, enter valid value.")
        await state.set_state(SettingsForm.target)
        return

    await state.update_data(value=value)
    await state.update_data(previous_state=SettingsForm.value)

    await message.answer(
        f"You entered {message.text}, is this correct?"
        f" Write 'exit' to exit update process",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Yes"),
                    KeyboardButton(text="No"),
                ]
            ],
            resize_keyboard=True,
        )
    )
    await state.set_state(SettingsForm.confirm)

@admin_router.message(SettingsForm.confirm)
async def confirm_settings_form(message: types.Message, state: FSMContext) -> None:
    """Confirm values for settings form.

    This function make sure admin is final
    about values he entered. If he is not
    then he will be sent back in terms of
    dialogue flow.

    Args:
        message: a message from the admin.
        state: a state object for dialogue.

    Returns:
        None, will send message according to the next dialogue step
        and redirect there.
    """

    response = message.text.lower().strip()
    data = await state.get_data()
    previous_state = data['previous_state']

    if response == "yes":
        if previous_state == SettingsForm.value:
            await message.answer("Thank you for your information!",
                                 reply_markup=ReplyKeyboardRemove())

            msg = await admin.update_settings(data['target'], data['value'])
            await message.answer(msg)

        else:
            logger.logger.error(f"There is no such Settings state: {previous_state}",
                                reply_markup=ReplyKeyboardRemove())
            await state.clear()

    elif response == "no":
        if previous_state == SettingsForm.value:
            await state.set_state(SettingsForm.value)

        else:
            logger.logger.error(f"There is no such Settings state: {previous_state}")

        await message.answer("You can reenter your data.",
                             reply_markup=ReplyKeyboardRemove())

    else:
        await message.answer("Your updating process has been stopped.",
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()



@admin_router.message(Command("link"))
async def link_user(message: types.Message,  state: FSMContext) -> None:
    """Process /link command from admin

    It will start dialogue that helps admin add
    new user-group relation into payments table.

    Args:
        message: a message from the admin.
        state: state object for dialogue.

    Returns:
        None, will send message according to the next dialogue step.
    """

    if (message.chat.type != ChatType.PRIVATE or
        not admin.is_admin(message.from_user.id)):
        return  # Only process DMs from admin

    await message.answer("Hey! Give me a username of a guy you want to link.\n"
                         "Telegram requires usernames to be from 5 to 32 letters long"
                         " and consists only of letters, numbers and underscores.\n"
                         "Also, please include '@' character.")
    await state.set_state(LinkForm.username)

@admin_router.message(LinkForm.username)
async def process_username(message: types.Message, state: FSMContext) -> None:
    """Process username value from admin.

    This function make sure admin will enter
    username correctly with Telegram specific validation.

    Args:
        message: a message from the admin.
        state: state object for dialogue.

    Returns:
        None, will send message according to the next dialogue step.
    """

    user = await admin.get_user(message.text)
    if (len(message.text) < 6 or len(message.text) > 33
            or not message.text.startswith('@')
            or not message.text.replace('_', '')[1:].isalnum()
            or user is None):
        await message.reply("This username is incorrect. Please try again.")

    else:
        await state.update_data(user_id=user[0])
        await state.update_data(previous_state=LinkForm.username)
        await message.answer(
            f"You entered {message.text}, is this correct?"
            f" Write 'exit' to exit link process",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text="Yes"),
                        KeyboardButton(text="No"),
                    ]
                ],
                resize_keyboard=True,
            )
        )
        await state.set_state(LinkForm.confirm)

@admin_router.message(LinkForm.group_name)
async def process_group_name(message: types.Message, state: FSMContext) -> None:
    """Process group name value from admin.

    This function make sure admin will enter
    group name correctly with Telegram specific validation.

    Args:
        message: a message from the admin.
        state: state object for dialogue.

    Returns:
        None, will send message according to the next dialogue step.
    """

    group = await admin.get_group(message.text)
    if len(message.text) > 255 or group is None:
        await message.reply("This group name is incorrect. Please try again.")

    else:
        await state.update_data(group_id=group[0])
        await state.update_data(payment_at=group[2])
        await state.update_data(previous_state=LinkForm.group_name)
        await message.answer(
            f"You entered {message.text}, is this correct?"
            f" Write 'exit' to exit link process",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text="Yes"),
                        KeyboardButton(text="No"),
                    ]
                ],
                resize_keyboard=True,
            )
        )
        await state.set_state(LinkForm.confirm)

@admin_router.message(LinkForm.payment_at)
async def process_payment_at(message: types.Message, state: FSMContext) -> None:
    """Process payment date value from admin.

    This function make sure admin will enter
    payment date correctly with logic specific validation.

    Args:
        message: a message from the admin.
        state: state object for dialogue.

    Returns:
        None, will send message according to the next dialogue step.
    """

    try:
        payment = datetime.strptime(message.text, '%Y-%m-%d')
    except ValueError:
        await message.answer("Your date is in wrong format. "
                             "It has to be in YYYY-MM-DD format,"
                             " e.g. 2025-06-24.")
        return

    await state.update_data(payment_at=payment)
    await state.update_data(previous_state=LinkForm.payment_at)

    await message.answer(
        f"You entered {message.text}, is this correct?"
        f" Write 'exit' to exit link process",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Yes"),
                    KeyboardButton(text="No"),
                ]
            ],
            resize_keyboard=True,
        )
    )
    await state.set_state(LinkForm.confirm)

@admin_router.message(LinkForm.confirm)
async def confirm_link_form(message: types.Message, state: FSMContext) -> None:
    """Confirm values for link form.

    This function make sure admin is final
    about values he entered. If he is not
    then he will be sent back in terms of
    dialogue flow.

    Args:
        message: a message from the admin.
        state: a state object for dialogue.

    Returns:
        None, will send message according to the next dialogue step
        and redirect there.
    """

    response = message.text.lower().strip()
    data = await state.get_data()
    previous_state = data['previous_state']

    if response == "yes":
        if previous_state == LinkForm.username:
            await message.answer("OK. Then, what is the name of the group he is in?",
                                 reply_markup=ReplyKeyboardRemove())
            await state.set_state(LinkForm.group_name)

        elif previous_state == LinkForm.group_name:
            date = data['payment_at'].strftime('%Y-%m-%d')

            await message.answer(f"Lastly, what is his payment date?"
                                 f"\nNote: this group default date is {date}."
                                 f"\n*Also, please provide data in YYYY-MM-DD format.",
                                 reply_markup=ReplyKeyboardRemove())
            await state.set_state(LinkForm.payment_at)

        elif previous_state == LinkForm.payment_at:
            await message.answer("Thank you for your information!",
                                 reply_markup=ReplyKeyboardRemove())

            ans = await admin.link_user_to_group(data['user_id'], data['group_id'], data['payment_at'])

            await message.answer(ans)
            await state.clear()

        else:
            logger.logger.error(f"There is no such LinkForm state: {previous_state}")
            await state.clear()

    elif response == "no":
        if previous_state == LinkForm.username:
            await state.set_state(LinkForm.username)

        elif previous_state == LinkForm.group_name:
            await state.set_state(LinkForm.group_name)

        elif previous_state == LinkForm.payment_at:
            await state.set_state(LinkForm.payment_at)

        else:
            logger.logger.error(f"There is no such LinkForm state: {previous_state}")

        await message.answer("Please, reenter your data.",
                             reply_markup=ReplyKeyboardRemove())

    else:
        await message.answer("Your linking process has been stopped.",
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()
