from typing import List, Optional

import asqlite
from discord.ext import commands


def benny_only() -> commands.check:
    async def predicate(ctx: commands.Context) -> None:
        """
        Check if the user is in the BennyBot server
        """
        if ctx.author.id in ctx.bot.user_manager.get_user(ctx.author.id).joined_server:
            return True
        raise commands.CheckFailure(
            "You must be in the BennyBot server to use this command."
        )

    return commands.check(predicate)


class User:
    """
    Represents a users data profile for the bot
    """

    def __init__(self, user: tuple, joined_server: bool) -> None:
        """
        Init with a tuple of the users data
        """
        self.user_id: str = user[0]
        self.premium_level: int = user[1]
        self.is_blacklisted: bool = user[2]
        self.timezone: Optional[str] = user[3]
        self.joined_server: bool = joined_server


class UserManager:
    """
    Class to access our users info
    """

    def __init__(self, bot: commands.Bot, database: asqlite.Connection) -> None:
        """
        Init with the userdb
        """
        self.bot = bot
        self.database = database
        self.users: List[User] = []

    async def get_user(self, user_id: int) -> Optional[User]:
        """
        Get a user from our database
        """
        for user in self.users:
            if user.user_id == str(user_id):
                return user
        await self.fetch_user(user_id)

    async def create_user(self, user_id: int) -> None:
        """
        Create a user in our small database
        """
        await self.database.execute(
            """INSERT INTO settings_users VALUES(?, ?, ?, ?);""",
            (str(user_id), 0, False, None),
        )
        await self.database.commit()

    async def fetch_user(self, user_id: int) -> tuple:
        """
        Get a users info
        """
        async with self.database.execute(
            """SELECT * FROM settings_users WHERE id = ?;""", (str(user_id),)
        ) as cursor:
            result = await cursor.fetchone()
            if not result:
                await self.create_user(user_id)
                return await self.get_user(user_id)
            return result

    async def load_users(self) -> None:
        """
        Load every single user that we know of into our database
        Does not contain any private information.
        """
        users_in_benny = set(
            member.id
            for member in (await self.bot.fetch_guild(993972438754922526)).members
        )

        for user in self.bot.users:
            self.users.append(
                User(await self.fetch_user(user.id), user.id in users_in_benny)
            )
