import discord
import discord.utils
from discord.ext import commands
from gears import style


class Info(commands.Cog):
    """
    This cog deals with levels
    """

    COLOR = style.Color.AQUA
    ICON = "ℹ️"

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

    @commands.command(
        name="permissions",
        description="""View a server members permissions.""",
        help="""View a server members permissions.""",
        brief="""Permissions of a member""",
        aliases=["perms"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 5.0, commands.BucketType.user)
    async def permissions_cmd(
        self, ctx: commands.Context, member: discord.Member = None
    ) -> None:
        """
        View an member permissions
        """
        if not member:
            member = ctx.author

        perms = member.guild_permissions
        perms = [perm for perm, value in perms if value]
        perms = '"\n"'.join(perms)

        embed = discord.Embed(
            title=f"{member.name}#{member.discriminator} Permissions",
            description=f"""```ahk
"{perms}"
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.random(),
        )
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """
    Setup the cog.
    """
    await bot.add_cog(Info(bot))
