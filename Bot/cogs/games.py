import asyncio
import discord
import discord.utils
from discord.ext import commands
from gears.style import c_get_color, c_get_emoji


class Games(commands.Cog):
    """Games to play with the bot"""

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Games(bot))
