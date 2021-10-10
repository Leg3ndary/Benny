import discord
from discord.ext import commands
import datetime
from gears.style import c_get_color, c_get_emoji
import asyncio

class Exalia(commands.Cog):
    """Moderation related commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hi(self, ctx):
        """Loser"""
        pass


def setup(bot):
    bot.add_cog(Exalia(bot))