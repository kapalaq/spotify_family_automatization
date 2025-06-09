import aiopg
import asyncio
from datetime import datetime
from SpotifyBot.app.config import DatabaseConfig

import sys
from typing import List, Tuple

# Fix for Windows + aiopg
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class Database:
    def __init__(self):
        cfg = DatabaseConfig()
        self.log = cfg.log_file
        self.dsn = (f"dbname={cfg.database} user={cfg.username.get_secret_value()} "
                    f"password={cfg.password.get_secret_value()} "
                    f"host={cfg.host} port={cfg.port}")
        self.pool = None


    def write_to_log(self, message: str, error: Exception = None) -> None:
        """
        Write exception to log file
        :param message: a message about where does exception occurred
        :param error: an error details
        :return: None
        """
        try:
            with open(self.log, 'a') as f:
                if error:
                    f.write(message + ' ' + error.__repr__() + '\n')
                else:
                    f.write(message + '\n')
        except Exception as e:
            print(e, file=sys.stderr)


    async def connect(self) -> bool:
        """
        Connect to database
        :return: whether database connection was successful
        """
        try:
            self.pool = await aiopg.create_pool(self.dsn)
        except Exception as e:
            self.write_to_log("ON TABLE INITALIZATION:", e)

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
                self.write_to_log("ON CONNECTION CLOSE:", e)
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
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        '''
                        CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL);
                        '''
                    )
                    await cur.execute(
                        '''
                        CREATE TABLE IF NOT EXISTS groups (
                        group_id INTEGER PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        deadline_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
                        '''
                    )
                    await cur.execute(
                        '''
                        CREATE TABLE IF NOT EXISTS group_members (
                        group_id INT NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
                        user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                        PRIMARY KEY (group_id, user_id));
                        '''
                    )
                    await cur.execute(
                        '''
                        CREATE TABLE IF NOT EXISTS payments (
                        group_id INT NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
                        user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                        paid BOOLEAN DEFAULT FALSE,
                        paid_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (group_id, user_id, paid_on));
                        '''
                    )
                    return True
                except Exception as e:
                    self.write_to_log("ON TABLE INITALIZATION:", e)
                    return False


    async def add_group(self, group_id: int) -> bool:
        """
        Add group to database
        :param group_id: a unique id of the group
        :return: whether the group was added successfully (T/F)
        :throw:
            Exception: Database connection failed.
            Exception: Group already exists.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "INSERT INTO groups (group_id) VALUES (%s)",
                        (group_id,)
                    )
                    return True
                except Exception as e:
                    self.write_to_log("ON GROUP ADD:", e)
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
                        f"""INSERT INTO users (user_id, username) VALUES (%s, %s);""",
                        (user_id, username)
                    )
                except Exception as e:
                    self.write_to_log("ON USER ADD:", e)
                return cursor.rowcount > 0


    async def get_user_by_id(self, user_id: int) -> Tuple[int, str]:
        """
        Get user from database
        :param user_id: a unique id of the user
        :return: (user_id, username) tuple
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT user_id, username FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                except Exception as e:
                    self.write_to_log("ON USER GET BY ID:", e)
                return await cur.fetchone()


    async def get_user_by_username(self, username: str) -> Tuple[int, str]:
        """
        Get user from database
        :param username: the username of the user
        :return: (user_id, username) tuple
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT user_id, username FROM users WHERE username = %s",
                        (username,)
                    )
                except Exception as e:
                    self.write_to_log("ON USER GET BY USERNAME:", e)
                return await cur.fetchone()


    async def get_group(self, group_id: int) -> Tuple[int, datetime, datetime]:
        """
        Get group from database
        :param group_id: id of the group
        :return: (group_id, created_at, deadline_at) tuple
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    res = await cur.execute(
                        "SELECT group_id, created_at, deadline_at FROM groups WHERE group_id = %s",
                        (group_id,)
                    )
                except Exception as e:
                    self.write_to_log("ON GROUP GET:", e)
                return res.fetchone()[0]


    async def link_user_to_group(self, user_id: int, group_id: int) -> bool:
        """
        Add User-group relation in the table
        :param user_id: User id
        :param group_id: Group id
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                    """
                        INSERT OR REPLACE INTO user_groups (user_id, group_id) VALUES (%s, %s)
                    """, (user_id, group_id)
                    )
                    return True
                except Exception as e:
                    self.write_to_log("ON USER-GROUPS RELATION ADD:", e)
                    return False


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
                cursor = await cur.execute(
                    "SELECT group_id FROM user_groups WHERE user_id = %s",
                    (user_id,)
                )
                row = await cursor.fetchone()
                return row[0] if row else None


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
            async with conn.cursor() as cur:
                cursor = await cur.execute(
                    "SELECT user_id FROM user_groups WHERE group_id = %s",
                    (group_id,)
                )
                return await cursor.fetchall()


    async def check_payment(self, user_id) -> bool:
        """
        Check whether the user paid
        :return: whether the user paid
        :throw:
            Exception: Database connection failed.
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")


        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                ans = await cur.execute("SELECT group_id, custom_day FROM groups")
                return await ans.fetchall()


    async def mark_payment(self, user_id, group_id) -> bool:
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                now = datetime.now().isoformat()
                await cur.execute("""
                    INSERT INTO payments (user_id, group_id, payment, timestamp)
                    VALUES (?, ?, 1, ?)
                    ON CONFLICT(user_id, group_id) DO UPDATE SET payment=1, timestamp=excluded.timestamp
                """, (user_id, group_id, now))
                await cur.commit()


    async def get_defaulters(self) -> List[Tuple[int, int]]:
        """
        Get all users that did not paid
        :return: List of users that was not paid
        """
        if not self.pool:
            raise Exception("Database connection pool is empty")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                query = """
                    SELECT g.group_id, p.user_id
                    FROM groups g
                    JOIN payments p ON g.group_id = p.group_id
                    WHERE EXTRACT(DAY FROM (CURRENT_TIMESTAMP() - g.deadile_at))
                    BETWEEN 1 and 4 AND p.paid = 0
                """
                try:
                    cursor = await cur.execute(query)
                except Exception as e:
                    self.write_to_log("ON DEFAULTERS GET:", e)
                return cursor.fetchall()


    async def get_statistic_per_group(self, group_id: int) -> List[int]:
        if not self.pool:
            raise Exception("Database connection pool is empty")
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                pass


    async def delete_user_from_group(self, user_id: int) -> bool:
        if not self.pool:
            raise Exception("Database connection pool is empty")
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                group = self.get_user_group(user_id)
                if group:
                    cur.execute("DELETE FROM user_groups WHERE user_id = %s")


    async def delete_group(self, group_id: int) -> bool:
        if not self.pool:
            raise Exception("Database connection pool is empty")
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                users = self.get_group_users(group_id)
                if len(users) > 0:
                    return False
                else:
                    return True


    async def delete_user(self, user_id: int) -> bool:
        if not self.pool:
            raise Exception("Database connection pool is empty")
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                group = self.get_user_group(user_id)
                if group:
                    return False
                else:
                    return True


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
            async with conn.cursor() as cur:
                try:
                    await cur.execute("DROP TABLE IF EXISTS user_groups")
                    await cur.execute("DROP TABLE IF EXISTS groups")
                    await cur.execute("DROP TABLE IF EXISTS payments")
                    await cur.execute("DROP TABLE IF EXISTS users")
                    return True
                except Exception as e:
                    self.write_to_log("ON DROP TABLE ERROR:", e)
                    return False
