import asyncio
import discord
import discord.utils
from discord.ext import commands
from gears import style


class CogExample(commands.Cog):
    """Cog Example Description"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="CommandName",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        usage="Usage",
        aliases=["None"],
        enabled=True,
        hidden=False,
    )
    async def my_command(self, ctx):
        """Command description"""


def setup(bot):
    bot.add_cog(CogExample(bot))
