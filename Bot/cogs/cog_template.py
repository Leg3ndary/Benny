import asyncio
import discord
import discord.utils
from discord.ext import commands
from discord import app_commands
from gears import style


class CogExample(commands.Cog):
    """Cog Example Description"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="command",
        description="""Description of command, complete overview with all neccessary info""",
        help="""More help""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def my_command(self, ctx):
        """Command description"""


async def setup(bot):
    await bot.add_cog(CogExample(bot))
