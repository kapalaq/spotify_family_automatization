"""admin.py user

This module is used to implement supporting class for admin commands.
It provides functions for all admin manipulations with database, config files.

Attributes:
    db: a Database object
"""

from typing import List, Tuple
from datetime import datetime
import pandas as pd

from app.config import TelegramConfig
from app.tools import ErrorLogger, Database
from app.tools import YAMLConfig as yC


db = Database()

class Admin:
    """Admin commands handling tool.

    This class allows user to handle all
    admin-specific functions with convenient
    functionality.

    Attributes:
        admin_id: a list of admin IDs to validate users
        logger: a ErrorLogger instance for error handling
    """

    admin_id: List[str] = TelegramConfig().admin_id
    logger: ErrorLogger = ErrorLogger()

    def is_admin(self, user_id: int) -> bool:
        """Check whether user is an admin.

        Function will compare provided ID with statically
        stored IDs of admins in config file protected by Pydantic.

        Args:
            user_id (int): A user unique ID.

        Returns:
            Whether user is an admin (True) or not (False).
        """

        return str(user_id) in map(lambda x: x.get_secret_value(), self.admin_id)

    @staticmethod
    async def update_settings(target: str, value: int) -> str:
        """Update settings variables using chat commands.

        This function allows admins to update settings variables
        from the chat directly using /update command.

        Args:
            target (str): a target settings variable.
            value (int): a new value for settings variable.

        Returns:
            Done! if update was successful. Apologize otherwise.
        """

        config = yC.load_config()

        if target == "price":
            try:
                config[target] = int(value)
                yC.save_config(config)
                return "Done!"
            except FileNotFoundError as e:
                Admin.logger.logger.error("ON CONFIG UPDATING: %s", e)
                return "Sorry! There is a problem with setting. Please, try again later!"

        else:
            return "Sorry! There is no such settings variable."

    @staticmethod
    async def link_user_to_group(user_id: int, group_id: int, payment_at: datetime=None) -> bool:
        """Links user to specified group and sets payment date.

        It creates a new row in a payments table with
        (group_id, user_id, payment_at) that links this user
        to the specified group.

        Args:
            user_id (int): a user ID of the user.
            group_id (int): a group ID of the specified group.
            payment_at (datetime): a date when the use has to pay his bill.

        Returns:
            Did insertion passed successfully (T/F).
        """
        return await db.add_payments(user_id, group_id, payment_at)

    async def get_unpaid_group(self) -> str:
        """Get all unpaid groups.

        It will include all groups that contains
        at least one unpaid user, meaning his
        payment date is behind current date.

        Returns:
            All unpaid users divided into groups
            and purely written as a string.
        """

        try:
            unpaid_users = await db.get_unpaid_group()
        except AttributeError as e:
            self.logger.logger.error("ON GET UNPAID GROUP: %s", e)
            return "Sorry! There is a problem with database."

        groups = (
            pd.DataFrame(
                unpaid_users,
                columns=["group_name", "user_name", "payment_at", "paid", "diff"]
            )
            .groupby("group_name")
        )
        num_of_groups = len(groups)

        ans = ""
        for group in groups:
            num_of_groups -= 1
            group_name, users = group

            ans += f"<b>{str(group_name).upper()}:</b>\n"
            for row in users.to_numpy():

                ans += "+-------------------+\n"
                if row[3]:
                    ans += f"| <i>PAID:</i>\n"
                else:
                    ans += f"| <i>UNPAID:</i>\n"

                ans += (f"|--- USERNAME: @{row[1]},\n"
                        f"|--- PAYMENT AT: {row[2].strftime("%d %B %Y, %H:%M")}.\n")

            ans += "+-------------------+\n"
            if num_of_groups != 0:
                ans += '\n=======================\n'

        return ans

    async def delete_user(self, username: str) -> bool:
        """Delete user instance by username.

        Args:
            username (str): Telegram username of the user.

        Returns:
            Whether user is deleted successfully (T/F).
        """

        try:
            response = await db.delete_user(username)
            return response
        except AttributeError as e:
            self.logger.logger.error("ON USER DELETE: %s", e)

    async def delete_group(self, group_name: str) -> bool:
        """Delete group instance by group name.

        Args:
            group_name (str): Telegram name of the group.

        Returns:
            Whether group is deleted successfully (T/F).
        """

        try:
            response = await db.delete_group(group_name)
            return response
        except AttributeError as e:
            self.logger.logger.error("ON GROUP DELETE: %s", e)

    async def get_user(self, username: str) -> Tuple[int, str]:
        """Get user ID by username.

        Args:
            username (str): Telegram username of the user.

        Returns:
            (User ID, username) if retrieved successfully, None otherwise.
        """

        try:
            user = await db.get_user_by_name(username)
            return user
        except AttributeError as e:
            self.logger.logger.error("ON GET USER: %s", e)

    async def get_group(self, group_name: str) -> Tuple[int, str, datetime, datetime]:
        """Get group ID by group name.

        Args:
            group_name (str): Telegram name of the group.

        Returns:
            (Group ID, group name, payment at, created at)
            if retrieved successfully, None otherwise.
        """

        try:
            group = await db.get_group_by_name(group_name)
            return group
        except AttributeError as e:
            self.logger.logger.error("ON GET GROUP: %s", e)

    async def add_group(self, group_id: int, group_name: str, date: str) -> bool:
        """Add group to database.

        Args:
            group_id (int): Telegram group ID.
            group_name (str): Telegram group name.
            date (str): Payment date of the group.

        Returns:
            Whether group is added successfully (T/F).
        """

        try:
            date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError as e:
            self.logger.logger.error("ON ADD GROUP: %s", e)
            return False

        response = await db.add_group(group_id, group_name, date)
        return response


if __name__ == '__main__':
    pass
