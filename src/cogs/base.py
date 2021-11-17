import discord
from discord.ext import commands
from discord.commands import slash_command, Option
from gears.style import c_get_color, c_get_emoji
import asyncio
import discord.utils


class Base(commands.Cog):
    """Cog Example Description"""

    def __init__(self, bot):
        self.bot = bot
        self.MemberConverter = commands.MemberConverter()

    @commands.command(
        name="avatar",
        description="""Enlarge the avatar of an user""",
        help="""Show a users avatar in a nice clean embed.""",
        brief="""Short help text""",
        usage="<User=Optional>",
        aliases=["av", "pfp"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def avatar(self, ctx, *, user: discord.Member = None):
        """Show a users avatar"""
        if not user:
            user = ctx.author

        embed = discord.Embed(
            title=user.display_name, timestamp=discord.utils.utcnow(), color=user.color
        )
        embed.set_image(url=user.avatar.url)
        await ctx.send(embed=embed)

    @slash_command(guild_ids=[787106686535860244])
    async def avatar(
        self, ctx, user: Option(str, "Enter someone's Name", required=False)
    ):
        """Show a users avatar"""
        user = await self.MemberConverter.convert(ctx, user)
        if not user:
            user = ctx.author
        embed = discord.Embed(
            title=user.display_name, timestamp=discord.utils.utcnow(), color=user.color
        )
        embed.set_image(url=user.avatar.url)
        await ctx.respond(embed=embed)

    @commands.command(
        name="info",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        usage="Usage",
        aliases=["i"],
        enabled=True,
        hidden=False,
    )
    async def my_command(self, ctx, person: discord.Member = None):
        """View an users info"""
        if not person:
            person = ctx.author

        embed = discord.Embed(
            title=f"",
            description=f"""""",
            timestamp=discord.utils.utcnow(),
            color=await c_get_color(),
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Base(bot))
