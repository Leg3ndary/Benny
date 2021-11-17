import discord
from discord.ext import commands
import discord.utils
from gears.style import c_get_color, c_get_emoji
import asyncio


class Exalia(commands.Cog):
    """Currency Game AKA Exalia"""

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Exalia(bot))
