from typing import List, Tuple
from datetime import datetime
import pandas as pd
from aiogram import types

from SpotifyBot.app.config import TelegramConfig
from SpotifyBot.app.tools import ErrorLogger, Database
from SpotifyBot.app.tools import YAMLConfig as yC


db = Database()


class Admin:
    admin_id: List[str] = TelegramConfig().admin_id
    logger: ErrorLogger = ErrorLogger()

    def is_admin(self, user_id: int) -> bool:
        """Check whether user is an admin.

        Function will compare provided ID with statically
        stored IDs of admins in config file protected by Pydantic.

        Args:
            user_id: A user unique ID.

        Returns:
            Whether user is an admin (True) or not (False).
        """
        return str(user_id) in map(lambda x: x.get_secret_value(), self.admin_id)

    @staticmethod
    async def update_settings(message: types.Message) -> None:
        """Update settings variables using chat commands.

        This function allows admins to update settings variables
        from the chat directly using /update command.

        Args:
            message: a message from admin that starts with /update

        Returns:
            None
        """
        parts = message.text.split(maxsplit=3)
        config = yC.load_config()
        if not 2 < len(parts) < 5:
            await message.answer(
                '\n'.join(f"{k}: {v}" for k, v in config.items()) + '\n\n'
                + "Usage: /update <KEY> <VALUE> <add/delete>\n"
                + "NOTE: <add/delete> does not work for price!"
            )
            return

        key, value = parts[1], parts[2]
        if key == "price":
            try:
                config[key] = int(value)
                yC.save_config(config)
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
                    yC.save_config(config)
                    await message.answer(f"Added {key} on {value} successfully!")
                except Exception as e:
                    await message.answer(f"Error adding {key}: {e}")
            elif action == "delete":
                try:
                    config[key].remove(value)
                    yC.save_config(config)
                    await message.answer(f"Deleted {value} from {key} successfully!")
                except Exception as e:
                    await message.answer(f"Error deleting {key}: {e}")
            else:
                await message.reply("There is no such action! Please, complete your query with 'add' or 'delete'.")
        else:
            await message.reply("There is no such key! Please, choose from provided list.")

    @staticmethod
    async def link_user_to_group(user_id: int, group_id: int, payment_at: datetime=None) -> str:
        """Links user to specified group and sets payment date.

        It creates a new row in a payments table with
        (group_id, user_id, payment_at) that links this user
        to the specified group.

        Args:
            user_id: a user ID of the user.
            group_id: a group ID of the specified group.
            payment_at: a date when the use has to pay his bill.

        Returns:
            Done!

        Raises:
            Username not found or Group name not found.
        """

        await db.add_payments(user_id, group_id, payment_at)
        return "Done!"

    async def get_unpaid_group(self, message: types.Message) -> None:
        """Get all unpaid groups.

        It will include all groups that contains
        at least one unpaid user, meaning his
        payment date is behind current date.

        Args:
            message: a message from admin that starts with /unpaid

        Returns:
            All unpaid users divided into groups
            and purely written as a string.
        """
        try:
            unpaid_users = await db.get_unpaid_group()
        except AttributeError as e:
            self.logger.logger.error("ON GET UNPAID GROUP: %s", e)
            return
        groups = (
            pd.DataFrame(
                unpaid_users,
                columns=["group_name", "user_name", "payment_at", "paid"]
            )
            .groupby("group_name")
        )
        num_of_groups = len(groups)

        ans = ""
        for group in groups:
            num_of_groups -= 1
            group_name, users = group
            ans += f"{group_name}:\n"
            for row in users.to_numpy():
                ans += f"- PAID: {row[2]} => ( USERNAME: {row[0]}, PAYMENT AT: {row[1]} )\n"
                ans += '\n'
            if num_of_groups != 0:
                ans += '\n=======================\n'

        await message.answer(ans)

    async def get_user(self, username: str) -> Tuple[int, str]:
        """Get user ID by username.

        Args:
            username: Telegram username of the user.

        Returns:
            (User ID, username) if retrieved successfully, None otherwise.
        """
        try:
            user = await db.get_user_by_name(username)
            return user
        except Exception as e:
            self.logger.logger.error("ON GET USER: %s", e)

    async def get_group(self, group_name: str) -> Tuple[int, str, datetime, datetime]:
        """Get group ID by group name.

        Args:
            group_name: Telegram name of the group.

        Returns:
            (Group ID, group name, payment at, created at)
            if retrieved successfully, None otherwise.
        """

        try:
            group = await db.get_group_by_name(group_name)
            return group
        except Exception as e:
            self.logger.logger.error("ON GET GROUP: %s", e)


if __name__ == '__main__':
    print(Admin().is_admin(708822452))
