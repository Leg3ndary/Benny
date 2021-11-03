import discord
from discord.ext import commands
import datetime
from gears.style import c_get_color, c_get_emoji
import asyncio


class Games(commands.Cog):
    """Games to play with the bot"""

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Games(bot))