import aiopg
import asyncio
import sys
from datetime import datetime
from typing import List, Tuple

from SpotifyBot.app.config import DatabaseConfig
from SpotifyBot.app.functions import logger

# Fix for Windows + aiopg
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class Database:

    def __init__(self):
        cfg = DatabaseConfig()
        self.dsn = (f"dbname={cfg.database} user={cfg.username.get_secret_value()} "
                    f"password={cfg.password.get_secret_value()} "
                    f"host={cfg.host} port={cfg.port}")
        self.pool = None

    async def connect(self) -> bool:
        """
        Connect to database
        :return: whether database connection was successful
        """
        try:
            self.pool = await aiopg.create_pool(self.dsn)
        except Exception as e:
            logger.error("ON CONNECTION: %s", e)

        return self.pool is None

    async def close(self) -> bool:
        """
        Close database connection
        :return: whether connection is closed
        """
        if self.pool:
            try:
                self.pool.close()
                await self.pool.wait_closed()
            except Exception as e:
                logger.error("ON CONNECTION CLOSE: %s", e)
            return True

    async def initialize(self) -> bool:
        """
        Initialize tables in Database
        :return: True if tables were successfully initialized
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    # Groups table
                    await cursor.execute(
                        '''
                        CREATE TABLE IF NOT EXISTS groups (
                        group_id INTEGER PRIMARY KEY,
                        group_name VARCHAR(100) UNIQUE,
                        payment_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
                        '''
                    )

                    # Users table with relation to groups
                    await cursor.execute(
                        '''
                        CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username VARCHAR(100) UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
                        '''
                    )

                    # Payments table
                    await cursor.execute(
                        '''
                        CREATE TABLE IF NOT EXISTS payments (
                        group_id INT NOT NULL,
                        user_id INT NOT NULL,
                        payment_at TIMESTAMP NOT NULL,
                        paid_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (group_id, user_id),
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                        FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE);
                        '''
                    )
                    return True
                except Exception as e:
                    logger.error("ON TABLE INITALIZATION: %s", e)
                    return False

    async def add_user(self, user_id: int, username: str) -> bool:
        """
        Add user to database
        :param user_id: a unique id of the user
        :param username: the username of the user
        :return: whether the user was added successfully (T/F)
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        "INSERT INTO users (user_id, username) VALUES (%s, %s);",
                        (user_id, username)
                    )
                except Exception as e:
                    logger.error("ON USER ADD: %s", e)
                return cursor.rowcount > 0

    async def get_user_by_id(self, user_id: int) -> Tuple[int, str]:
        """
        Get user from database table by ID
        :param user_id: a unique id of the user
        :return: (userID, username) tuple
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        "SELECT user_id, username FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    return await cursor.fetchone()
                except Exception as e:
                    logger.error("ON USER GET BY ID: %s", e)

    async def get_user_by_name(self, username: str) -> Tuple[int, str]:
        """
        Get user from database table by username
        :param username: username of the user
        :return: (userID, username) tuple
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        "SELECT user_id, username FROM users WHERE username = %s",
                        (username,)
                    )
                    return await cursor.fetchone()
                except Exception as e:
                    logger.error("ON USER GET BY USERNAME: %s", e)

    async def update_username(self, user_id: int, new_username: str) -> bool:
        """
        Update username in database table
        :param user_id: a unique id of the user
        :param new_username: the new username
        :return: whether the username was updated successfully (T/F)
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        "UPDATE users SET username = %s WHERE user_id = %s",
                        (new_username, user_id)
                    )
                except Exception as e:
                    logger.error("ON USERNAME UPDATE BY ID: %s", e)
                return cursor.rowcount > 0

    async def add_group(self, group_id: int, group_name: str, payment_at: datetime) -> bool:
        """
        Add group to database
        :param group_id: a unique id of the group
        :param group_name: a unique group name
        :param payment_at: a payment date
        :return: whether the group was added successfully (T/F)
        :throw:
            Exception: Database connection failed.
            Exception: Group already exists.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        "INSERT INTO groups (group_id, group_name, payment_at) VALUES (%s, LOWER(%s), %s)",
                        (group_id, group_name, payment_at)
                    )
                except Exception as e:
                    logger.error("ON GROUP ADD: %s", e)
                return cursor.rowcount > 0

    async def get_group(self, group_id: int) -> Tuple[int, str, datetime, datetime]:
        """
        Get group from database table
        :param group_id: id of the group
        :return: (group_id, group_name, payment_at, created_at) tuple
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        "SELECT group_id, group_name, payment_at, created_at FROM groups WHERE group_id = %s",
                        (group_id,)
                    )
                    return await cursor.fetchone()
                except Exception as e:
                    logger.error("ON GROUP GET: %s", e)

    async def get_group_by_name(self, group_name: str) -> Tuple[int, str, datetime, datetime]:
        """
        Get group from database table by name
        :param group_name: name of the group
        :return: (group_id, group_name, payment_at, created_at) tuple
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        SELECT group_id, group_name, payment_at, created_at
                        FROM groups WHERE LOWER(group_name) = %s
                        """,
                        (group_name,)
                    )
                    return await cursor.fetchone()
                except Exception as e:
                    logger.error("ON GROUP GET BY NAME: %s", e)

    async def update_group_name(self, group_id: int, new_group_name: str) -> bool:
        """
        Update group name in database table
        :param group_id: a unique id of the group
        :param new_group_name: the new group name
        :return: whether the group name was updated successfully (T/F)
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        "UPDATE groups SET group_name = LOWER(%s) WHERE group_id = %s",
                        (new_group_name, group_id)
                    )
                except Exception as e:
                    logger.error("ON GROUP NAME UPDATE BY ID: %s", e)
                return cursor.rowcount > 0

    async def add_payments(self, user_id: int, group_id: int, payment_at: datetime) -> bool:
        """
        Add User-group relation in the table
        :param user_id: user id
        :param group_id: group id
        :param payment_at: payment date
        :return: whether the relation was added successfully (T/F)
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """INSERT OR REPLACE INTO payments (user_id, group_id, payment_at)
                        VALUES (%s, %s, %s)""",
                        (user_id, group_id, payment_at)
                    )
                except Exception as e:
                    logger.error("ON PAYMENTS RELATION ADD: %s", e)
                return cursor.rowcount > 0

    async def get_user_group(self, user_id: int) -> int:
        """
        Get user's group from the table
        :param user_id:
        :return: Group id
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    cursor = await cur.execute(
                        "SELECT group_id FROM payments WHERE user_id = %s",
                        (user_id,)
                    )
                    return await cursor.fetchone()
                except Exception as e:
                    logger.error("ON USER'S GROUP GET: %s", e)

    async def get_group_users(self, group_id: int) -> List[int]:
        """
        Get group's users from the table
        :param group_id:
        :return: User id
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        "SELECT user_id FROM payments WHERE group_id = %s",
                        (group_id,)
                    )
                    return await cursor.fetchall()
                except Exception as e:
                    logger.error("ON GROUP USERS GET: %s", e)

    async def check_payments(self) -> List[Tuple[int, int, int]]:
        """
        Check whether the users paid
        :return: List[Tuple[int, int, int, bool]]: (groupID, userID, days until payment)
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        SELECT group_id, user_id,
                        TIMESTAMPDIFF(DAY, payment_at, CURRENT_TIMESTAMP) as diff,
                        FROM groups
                        WHERE diff >= 0
                        """,
                    )
                    return await cursor.fetchall()
                except Exception as e:
                    logger.error("ON CHECK PAYMENT: %s", e)

    async def mark_payment(self, user_id: int, month_paid: int) -> bool:
        """
        Add user payment into database table
        :param user_id: a unique id of the user
        :param month_paid: how many month in advance he paid
        :return: whether the user was added successfully (T/F)
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    now = datetime.now().isoformat()
                    await cursor.execute(
                        """
                        UPDATE payments
                        SET payment_at = payment_at + (%s || ' months')::INTERVAL
                            paid_on = %s
                        WHERE user_id = %s
                        """,
                        (month_paid, now, user_id)
                    )
                except Exception as e:
                    logger.error("ON MARK PAYMENT: %s", e)
                return cursor.rowcount > 0

    async def get_statistic_per_group(self, group_name: str) -> List[Tuple[str, datetime, datetime]]:
        """
        Get statistic of payments per group
        :param group_name: name of the group
        :return:
            List[Tuple[int, str, datetime, datetime]]:
                list of (username, next payment date, last payment date)
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    group_id = await self.get_group_by_name(group_name)
                    await cursor.execute(
                        """
                        SELECT u.username, p.payment_at,
                        TIMESTAMPDIFF(DAY, p.payment_at, CURRENT_TIMESTAMP) as diff
                        FROM payments p
                        INNER JOIN users u
                        ON p.user_id = u.user_id
                        WHERE group_id = %s
                        """,
                        (group_id,)
                    )
                    return await cursor.fetchall()
                except Exception as e:
                    logger.error("ON GROUP STATISTIC GET: %s", e)

    async def delete_user(self, username: str) -> bool:
        """
        Delete user from database table
        :param username: username of the user
        :return: whether the user was deleted successfully (T/F)
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        "DELETE FROM users WHERE username = %s",
                        (username,)
                    )
                except Exception as e:
                    logger.error("ON DELETE FROM USERS: %s", e)
                return cursor.rowcount > 0

    async def delete_group(self, group_name: str) -> bool:
        """
        Delete group from database table
        :param group_name: name of the group
        :return: whether the group was deleted successfully (T/F)
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        "DELETE FROM groups WHERE group_name = %s",
                        (group_name,)
                    )
                except Exception as e:
                    logger.error("ON DELETE FROM GROUPS: %s", e)
                return cursor.rowcount > 0

    async def drop_tables(self) -> bool:
        """
        Drop all tables for debug purposes
        :return: whether tables were dropped
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute("DROP TABLE IF EXISTS users CASCADE")
                    await cursor.execute("DROP TABLE IF EXISTS groups CASCADE")
                    await cursor.execute("DROP TABLE payment")
                    return True
                except Exception as e:
                    logger.error("ON DROP TABLE ERROR: %s", e)
                    return False
