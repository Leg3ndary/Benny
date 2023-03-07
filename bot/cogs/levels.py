import asyncio

import asqlite
import discord
import discord.utils
from discord.ext import commands
from gears import style


class Levels(commands.Cog):
    """
    This cog deals with levels
    """

    COLOR = style.Color.GREEN
    ICON = "🎚️"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Construct the levels cog
        """
        self.bot = bot

    async def cog_load(self) -> None:
        """
        Load the cog
        """
        async with asqlite.connect("database.db") as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS levels (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    level INTEGER NOT NULL,
                    xp INTEGER NOT NULL,
                    PRIMARY KEY (user_id, guild_id)
                )
                """
            )
            await db.commit()


async def setup(bot: commands.Bot) -> None:
    """
    Setup the cog.
    """
    # await bot.add_cog(Levels(bot))
