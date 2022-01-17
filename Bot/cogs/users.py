import asqlite
import discord
import discord.utils
from discord.ext import commands
from gears import style


class Users(commands.Cog):
    """Cog Example Description"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_load_users(self):
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
        await self.bot.printer.print_load("Users")


def setup(bot):
    bot.add_cog(Users(bot))
