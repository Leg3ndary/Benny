import asyncio
import discord
import discord.utils
from discord.ext import commands
from gears import style


class Games(commands.Cog):
    """Games to play with the bot"""

    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Games(bot))
