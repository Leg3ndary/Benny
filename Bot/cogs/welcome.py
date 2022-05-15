import asyncio  
import discord
import discord.utils
from discord.ext import commands
from gears import style


class Welcome(commands.Cog):
    """
    Anything to deal with welcoming or leaving"""

    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(Welcome(bot))