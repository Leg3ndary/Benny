import asyncio
import discord
import discord.utils
from discord.ext import commands
from gears import style


class Exalia(commands.Cog):
    """Currency Game AKA Exalia"""

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Exalia(bot))
