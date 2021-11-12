import discord
from discord.ext import commands
import datetime

from discord.ext.commands.core import bot_has_any_role
from gears.style import c_get_color, c_get_emoji
import asyncio


class Base(commands.Cog):
    """Cog Example Description"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="avatar",
        description="""Enlarge the avatar of an user""",
        help="""Show a users avatar in a nice clean embed.""",
        brief="""Short help text""",
        usage="<User=Optional>",
        aliases=["av", "pfp"],
        enabled=True,
        hidden=False
    )
    async def avatar(self, ctx, *, user: discord.Member = None):
        """Show a users avatar"""
        if not user:
            user = ctx.author

        embed = discord.Embed(
            title=user.display_name,
            timestamp=datetime.datetime.utcnow(),
            color=user.color()
        )
        embed.set_image(
            url=user.avatar_url
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Base(bot))
