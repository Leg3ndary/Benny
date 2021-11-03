from pbwrap import Pastebin
import os
import discord
from discord.ext import commands
import datetime
from gears.style import c_get_color, c_get_emoji
import asyncio

'''
print(pastebin.create_paste(
    api_paste_code="""class Pastebin(commands.Cog):
    def __init__(self):
        pass""",
    api_paste_private=1,
    api_paste_name="Error test",
    api_paste_expire_date="N",
    api_paste_format="python"
))
'''


class Pastebin(commands.Cog):
    """Moderation related commands"""

    def __init__(self, bot):
        self.bot = bot
        bot.pastebin = Pastebin(os.getenv("Pastebin_Token"))

    @commands.group(name="pastebin", aliases=["pb"])
    async def pastebin_commands(self, ctx):
        """Loser"""
        if not ctx.invoked_subcommand:
            pass

    @pastebin_commands.command()
    async def create(self, ctx):
        """Things"""

    @commands.Cog.listener()
    async def on_create_error_pastebin(self, name, id, error):
        """Create a pastebin"""
        return self.bot.pastebin.create_paste(
            api_paste_code=error,
            api_paste_private=1,
            api_paste_name="Error test",
            api_paste_expire_date="N",
            api_paste_format="python",
        )


def setup(bot):
    bot.add_cog(Pastebin(bot))