import asqlite
import discord
import discord.utils
from discord.ext import commands
from gears import style


class UserAccess:
    """
    Class to access our users info
    """

    def __init__(self, db) -> None:
        """Init with the userdb"""
        self.db = db

    async def create_user(self, user_id: str) -> tuple:
        """Create a user in our small database"""
        async with self.db as db:
            await db.execute("""INSERT INTO users VALUES(?, 0, False);""", (user_id,))
            await db.commit()

    async def get_user(self, user_id: str) -> tuple:
        """Get a users info"""
        async with self.db as db:
            async with db.execute(
                """SELECT * FROM users WHERE user_id = ?;""", (user_id,)
            ) as cursor:
                if not cursor.fetchone():
                    # Uh oh, user wasn't found, time to create a profile for them
                    await self.create_user(user_id)
                    # Gasp scary recursion
                    return await self.get_user(user_id)
                else:
                    return cursor.fetchone()


class Users(commands.Cog):
    """Cog Example Description"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        """Load up our users yay"""
        async with asqlite.connect("Databases/users.db") as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id           TEXT    PRIMARY KEY
                                        NOT NULL,
                    patron_level INTEGER NOT NULL
                                        DEFAULT (0),
                    blacklisted  BOOLEAN DEFAULT (False) 
                                        NOT NULL
                );
                """
            )
        self.bot.usersDB = await asqlite.connect("Databases/users.db")

        async with self.bot.usersDB as db:
            await db.execute(
                """
                
                """
            )
        await self.bot.printer.print_load("Users")


async def setup(bot):
    await bot.add_cog(Users(bot))
