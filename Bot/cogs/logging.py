import asyncio
import asqlite
import discord
import discord.utils
from discord.ext import commands
from gears import style


class Logging(commands.Cog):
    """Cog Example Description"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self) -> None:
        """
        On Cog Load
        """



async def setup(bot):
    await bot.add_cog(Logging(bot))
