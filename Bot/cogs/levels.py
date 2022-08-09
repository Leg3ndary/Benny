import asyncio

import discord
import discord.utils
from discord.ext import commands
from gears import style


class Levels(commands.Cog):
    """
    This cog deals with levels
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Construct the levels cog
        """
        self.bot = bot


async def setup(bot: commands.Bot) -> None:
    """
    Setup the cog.
    """
    await bot.add_cog(Levels(bot))
