"""Forms module.

This module provides implementations for all
scenarios of forms that bot has.
"""

from aiogram.fsm.state import State, StatesGroup


class SettingsForm(StatesGroup):
    """Settings Form.

    A form to change some system settings.

    Attributes:
        target (State): state to process a target.
        value (State): state to process a value.
        confirm (State): state to confirm a value.
    """

    target = State()
    value = State()
    confirm = State()


class LinkForm(StatesGroup):
    """Link Form.

    A form to link user to group using payment table.

    Attributes:
        username (State): state to process a username.
        group_name (State): state to process a group name.
        payment_at (State): state to process a payment date.
        confirm (State): state to confirm username/group name/payment date.
    """

    username = State()
    group_name = State()
    payment_at = State()
    confirm = State()


class DeleteForm(StatesGroup):
    """Delete Form.

    A form to delete user/group from database.

    Attributes:
        target (State): state to process a target.
        value (State): state to process a value.
        confirm (State): state to confirm a value.
    """

    target = State()
    value = State()
    confirm = State()


class PayForm(StatesGroup):
    """Payment Form.

    A form to pay for subscription.

    Attributes:
        months (State): state to process a chosen period.
        confirm (State): state to confirm a chosen period.
        payment (State): state to process a payment.
    """

    months = State()
    confirm = State()
    payment = State()
