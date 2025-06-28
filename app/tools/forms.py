from aiogram.fsm.state import State, StatesGroup


class SettingsForm(StatesGroup):
    target = State()
    value = State()
    confirm = State()


class LinkForm(StatesGroup):
    username = State()
    group_name = State()
    payment_at = State()
    confirm = State()
