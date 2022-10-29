import asyncio

import asqlite
import discord
import discord.utils
from discord.ext import commands
from gears import style


class MemberView(discord.ui.View):
    """
    MemberView for members we wanna view
    """

    def __init__(self, member: discord.Member) -> None:
        """
        MemberView for members we wanna view
        """
        self.member = member
        super().__init__()


class Info(commands.Cog):
    """
    This cog deals with levels
    """

    COLOR = style.Color.GREEN
    ICON = ":floppy_disk:"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Construct the levels cog
        """
        self.bot = bot

    @commands.hybrid_command(
        name="info",
        description="""View a server members info including roles, create, and join times.""",
        help="""View a server members info including roles, create, and join times.""",
        brief="""Info about a member""",
        aliases=["i"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 5.0, commands.BucketType.user)
    async def info_cmd(
        self, ctx: commands.Context, member: discord.Member = None
    ) -> None:
        """
        View an member info
        """
        if not member:
            member = ctx.author

        embed = discord.Embed(
            title=f"{member.name}#{member.discriminator}",
            timestamp=discord.utils.utcnow(),
            color=member.color,
        )
        embed.add_field(
            name="Created At",
            value=discord.utils.format_dt(member.created_at, "F"),
            inline=False,
        )
        embed.add_field(
            name="Joined At",
            value=discord.utils.format_dt(member.joined_at, "F"),
            inline=False,
        )
        embed.add_field(
            name="Roles",
            value=" ".join(reversed([role.mention for role in member.roles[1:43]])),
            inline=False,
        )
        embed.set_author(
            name=member.display_name,
            icon_url=member.display_icon.url if member.display_icon else None,
        )
        embed.set_footer(
            text=f"{member.id}{' - This user is a bot.' if member.bot else ''}",
        )
        embed.set_thumbnail(
            url=member.display_avatar.url
            if member.display_avatar
            else member.avatar.url
        )
        await ctx.reply(embed=embed)

    # Make a permissions command along with a more complicated info view for above


async def setup(bot: commands.Bot) -> None:
    """
    Setup the cog.
    """
    # await bot.add_cog(Info(bot))
