import discord
import discord.utils
from discord.commands import Option, slash_command
from discord.ext import commands
from gears import cviews, style
import unicodedata


"""@commands.dynamic_cooldown(custom_cooldown, commands.BucketType.user)
async def ping(ctx):
    await ctx.send("pong")"""


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
        aliases=["av", "pfp"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def avatar_cmd(self, ctx, *, user: discord.Member = None):
        """Show a users avatar"""
        view = cviews.DeleteView()
        if not user:
            user = ctx.author

        embed = discord.Embed(
            title=user.display_name, timestamp=discord.utils.utcnow(), color=user.color
        )
        embed.set_image(url=user.avatar.url)
        view.bctx = await ctx.send(embed=embed, view=view)

    @slash_command()
    async def avatar(
        self, ctx, user: Option(str, "Enter someone's Name", required=False)
    ):
        """Show a users avatar"""
        view = cviews.DeleteView(True)
        if not user:
            user = ctx.author
        else:
            user = await self.MemberConverter.convert(ctx, user)
        embed = discord.Embed(
            title=user.display_name, timestamp=discord.utils.utcnow(), color=user.color
        )
        embed.set_image(url=user.avatar.url)
        view.bctx = await ctx.respond(embed=embed, view=view)

    @commands.command(
        name="info",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        aliases=["i"],
        enabled=True,
        hidden=False,
    )
    async def my_command(self, ctx, person: discord.Member = None):
        """View an users info"""
        if not person:
            person = ctx.author

        embed = discord.Embed(
            title=f"{person.name}#{person.discriminator} Info",
            description=f"""
            {person.bot}
            {person.created_at}
            {person.display_name}
            {person.id}
            {person.mention}
            {person.mutual_guilds}
            {person.public_flags}
            {person.system}""",
            timestamp=discord.utils.utcnow(),
            color=person.color,
        )
        embed.set_thumbnail(url=person.avatar)
        await ctx.send(embed=embed)

    @commands.command(
        name="charinfo",
        aliases=["ci"],
        description="""Get some charinfo yay""",
        help="""Evaluate some code, dev only.""",
        brief="Get one or multiple characters info",
        enabled=True,
        hidden=False,
    )
    async def charinfo(self, ctx, *, characters: str):
        """Gives you the character info"""

        def to_string(c):
            digit = f"{ord(c):x}"
            name = unicodedata.name(c, "Name not found.")
            return f"""```fix
\\U{digit:>08}
```
{c} - [{name}](http://www.fileformat.info/info/unicode/char/{digit})"""

        msg = "\n".join(map(to_string, characters))

        embed = discord.Embed(
            title="Charinfo",
            description=msg,
            timestamp=discord.utils.utcnow(),
            color=style.get_color(),
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Base(bot))
