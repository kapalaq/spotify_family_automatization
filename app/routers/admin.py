"""admin.py router

This module is used to implement router for admin commands.
It includes all commands except the general for both
admin and user commands.

Attributes:
    admin_router (Router): a Router object to control flow.
    admin (Admin): a supporting class with Admin specific functions.
    storage (MemoryStorage): a memory storage for forms.
    logger (ErrorLogger): a logger object to control logging.
"""

from datetime import datetime
from aiogram import Router, types
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from app.tools import LinkForm, SettingsForm, DeleteForm
from app.tools import ErrorLogger, YAMLConfig
from .users.admin import Admin


admin_router = Router()
admin = Admin()
storage = MemoryStorage()

logger = ErrorLogger()

@admin_router.message(Command("start"))
async def start(message: types.Message):
    """Start command handler.

    This function handles first launch and
    /start command. It provides user with
    introduction and basic functionality.

    Args:
        message (types.Message): the message to be processed.

    Returns:
        None, welcome message.
    """

    if not admin.is_admin(message.from_user.id):
        return # process commands only from admin

    if message.chat.type == ChatType.GROUP:
        ans = """
<b>He-e-y! 🤖 Spotify Bot here.</b>
I help people connect to <b>Spotify Family Subscription</b>🎵.

To make everything clear, I provide you with list of all commands 📋.
If you want get detailed info about them, write <b>/help</b> ℹ️

<b>Users:</b>
- <i>/add_me</i> : adds you in database 🔄.

<b>Admin:</b>
- <i>/add_me [date]</i> : adds group in database 🔄.
"""

    elif message.chat.type == ChatType.PRIVATE:
        ans = """
<b>He-e-y! 🤖 Spotify Bot here.</b>
I help people connect to <b>Spotify Family Subscription</b>🎵.
My goal is to help you handle all these users 👥.
Feel free to contact the main developer if you have any questions: @kapalaq 💬

To make everything clear, I provide you with list of all commands 📋.

- <b>/unpaid</b> : shows you all unpaid users 💸.
- <b>/delete</b> : allows you to delete user/group
- <b>/update</b> : allows you to update some variables 🔄.
- <b>/link</b> : a manual user to group linking process 🔗.
"""

    else:
        ans = "This chat is <b>not supported</b> in current version."

    await message.answer(ans, parse_mode="HTML")



@admin_router.message(Command("unpaid"))
async def get_unpaid(message: types.Message):
    """Get all unpaid groups.

    This function returns all groups that
    contains at least one unpaid user.
    In accordance with inner logic of Database,
    a user is classified as unpaid if his payment
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

    if response is None or response == '':
        response = "There are no unpaid groups."

    await message.answer(response, parse_mode="HTML")



@admin_router.message(Command('add_me'))
async def add_me_cmd(message: types.Message) -> None:
    """Add group command.

    This function process /add_me command that, in admin case,
    saves group into database.

    Args:
        message: a message from the admin.

    Returns:
        None, will send message of status.
    """

    if (message.chat.type != ChatType.GROUP or
        not admin.is_admin(message.from_user.id)):
        return # process only messages in groups from admin
    try:
        date = message.text.strip().lower().split()[1]
    except IndexError:
        date = datetime.now().strftime('%Y-%m-%d')
        await message.answer(
            f"Since you did not specify a date, {date} will be used."
        )

    await admin.add_group(message.chat.id, message.chat.title, date)
    await message.reply("Done!", parse_mode="HTML")



@admin_router.message(Command("delete"))
async def delete_cmd(message: types.Message,  state: FSMContext) -> None:
    """Process /delete command from admin

    It will start dialogue that helps admin
    delete user or group.

    Args:
        message: a message from the admin.
        state: state object for dialogue.

    Returns:
        None, will send message according to the next dialogue step.
    """

    if (message.chat.type != ChatType.PRIVATE or
        not admin.is_admin(message.from_user.id)):
        return  # Only process DMs from admin

    await message.answer("Hey! What do you want to delete?",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 [
                                     KeyboardButton(text="user"),
                                     KeyboardButton(text="group"),
                                 ]
                             ],
                             resize_keyboard=True,
                         ))
    await state.set_state(DeleteForm.target)

@admin_router.message(DeleteForm.target)
async def process_delete_target(message: types.Message, state: FSMContext) -> None:
    """Process type value from admin.

    This function make sure admin will enter
    type correctly with logic specific validation.

    Args:
        message: a message from the admin.
        state: state object for dialogue.

    Returns:
        None, will send message according to the next dialogue step.
    """

    target = message.text.strip().lower()

    if target == 'user':
        await message.answer(
            "Please, provide me with username of the person you want to delete.\n"
            "Note: Telegram requires usernames to be from 5 to 32 letters long.\n"
            "It also have to consist only of letters, numbers and underscores.\n"
            "Please include '@' character.",
            reply_markup=ReplyKeyboardRemove()
        )

    elif target == 'group':
        await message.answer(
            "Please, provide me with name of the group you want to delete.\n"
            "Note: Telegram requires group names to be up to 255 letters long.\n",
            reply_markup=ReplyKeyboardRemove()
        )

    else:
        await message.answer(
            f"There are no settings named {target}. Please try again."
        )
        await state.set_state(SettingsForm.target)
        return

    await state.update_data(target=target)
    await state.set_state(DeleteForm.value)

@admin_router.message(DeleteForm.value)
async def process_delete_value(message: types.Message, state: FSMContext) -> None:
    """Process name on delete from admin.

    This function make sure admin will enter
    name on delete correctly with Telegram specific validation.

    Args:
        message: a message from the admin.
        state: state object for dialogue.

    Returns:
        None, will send message according to the next dialogue step.
    """

    value = message.text.strip()
    data = await state.get_data()

    if data['target'] == 'user':

        user = await admin.get_user(value)
        if (len(message.text) < 6 or len(message.text) > 33
                or not message.text.startswith('@')
                or not message.text.replace('_', '')[1:].isalnum()
                or user is None):
            await message.reply("This username is incorrect. Please try again.")
            await state.set_state(DeleteForm.value)
            return

    elif data['target'] == 'group':

        group = await admin.get_group(value)
        if len(message.text) > 255 or group is None:
            await message.reply("This group name is incorrect. Please try again.")
            await state.set_state(DeleteForm.value)
            return

    else:
        logger.logger.error(
            f"ON DELETION PROCEESS: UNKNOWN VALUE FOR TARGET ATTRIBUTE: {data['target']}"
        )
        await state.clear()
        return

    await message.answer(
        f"You entered {value}, is this correct?\n"
        f"Note: Delete operation cannot be reverted and "
        f"requires pass all addition process from the start "
        f"if you will ever change your mind.\n"
        f"<b>ALL</b> connected payments to specified "
        f"<i>username/group name</i> will be also deleted.\n\n"
        f"Write 'exit' to exit update process.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Yes"),
                    KeyboardButton(text="No"),
                ]
            ],
            resize_keyboard=True,
        ),
    )
    await state.update_data(value=value)
    await state.set_state(DeleteForm.confirm)

@admin_router.message(DeleteForm.confirm)
async def confirm_delete_form(message: types.Message, state: FSMContext) -> None:
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

    if response == "yes":
        await message.answer("Thank you for your information!",
                             reply_markup=ReplyKeyboardRemove())

        if data['target'] == 'user':
            response = await admin.delete_user(data['value'])

        elif data['target'] == 'group':
            response = await admin.delete_group(data['value'])

        sorry = "Sorry!, there is a problem with our server. Please try again later."
        msg = "Done!" if response else sorry
        await message.answer(msg)

        await state.clear()

    elif response == "no":
        await message.answer("You can reenter your data.",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(DeleteForm.value)

    else:
        await message.answer("Your deletion process has been stopped.",
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()



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
async def process_update_target(message: types.Message, state: FSMContext) -> None:
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
async def process_update_value(message: types.Message, state: FSMContext) -> None:
    """Process update value from admin.

    This function make sure admin will enter
    value for update correctly with logic specific validation.

    Args:
        message: a message from the admin.
        state: state object for dialogue.

    Returns:
        None, will send message according to the next dialogue step.
    """

    try:
        value = int(message.text.strip())
    except ValueError:
        await message.answer("Your value is invalid. Please, enter valid value.")
        await state.set_state(SettingsForm.value)
        return

    if int(message.text.strip()) <= 0:
        await message.answer("Your value is less or equal to 0. Please, enter valid value.")
        await state.set_state(SettingsForm.value)
        return

    await state.update_data(value=value)

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

    if response == "yes":
        await message.answer("Thank you for your information!",
                             reply_markup=ReplyKeyboardRemove())

        msg = await admin.update_settings(data['target'], data['value'])
        await message.answer(msg)

        await state.clear()

    elif response == "no":
        await state.set_state(SettingsForm.value)
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
            ans = await admin.link_user_to_group(
                data['user_id'], data['group_id'], data['payment_at']
            )

            if ans:
                await message.answer("Done!")
            else:
                await message.answer("Sorry! Such relation already exists.")

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
            await state.clear()

        await message.answer("Please, reenter your data.",
                             reply_markup=ReplyKeyboardRemove())

    else:
        await message.answer("Your linking process has been stopped.",
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()
