import asyncio
import discord
import discord.utils
import datetime
from discord.ext import commands, tasks
from gears import style


class PremiumToken:
    """
    Premium token, exchanges for a months worth of premium for a server (30 days)
    """

    def __init__(self) -> None:
        """
        Construct token data
        """

    async def exchange(self, server: int) -> bool:
        """
        Exchange the token for premium for 30 days
        """
        


class PremiumSubscriber:
    """
    Premium subscriber, contains relevant information about subscribers
    """

    def __init__(self) -> None:
        """
        Construct subscriber data
        """


class PremiumManager:
    """
    Manages premium memberships
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init for premium memberships
        """
        self.bot = bot

    async def get_premium(self, server: int) -> PremiumToken:
        """
        Return a servers premium
        """

    async def get_subscription(self, user: int) -> PremiumSubscriber:
        """
        Return a users subscription details 
        """

    async def check_expiry(self, user: int) -> bool:
        """"""


class Premium(commands.Cog):
    """Cog Example Description"""

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init Premium
        """
        self.bot = bot

    @commands.command(
        name="command",
        description="""Description of command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def my_command(self, ctx: commands.Context) -> None:
        """Command description"""


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Premium(bot))