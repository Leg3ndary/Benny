import discord
import discord.utils
import time
import unicodedata
from discord.ext import commands
from gears import cviews, style


"""@commands.dynamic_cooldown(custom_cooldown, commands.BucketType.user)
async def ping(ctx):
    await ctx.send("pong")"""


class Base(commands.Cog):
    """Cog Example Description"""

    def __init__(self, bot):
        self.bot = bot
        self.MemberConverter = commands.MemberConverter()

    @commands.command(
        name="about",
        description="""tells you some stuff about the bot""",
        help="""About the bot, why I built it, what it can and is going to do""",
        brief="About the bot",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.channel)
    async def about_cmd(self, ctx):
        """About command"""
        embed = discord.Embed(
            title=f"About the Bot",
            description=f"""A Bot I've made for fun, friends and learning python.""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("aqua"),
        )
        embed.set_footer(
            text="_Leg3ndary#5759",
            icon_url="https://cdn.discordapp.com/avatars/360061101477724170/798fd1d22b6c219236ad97be44aa425d.png?size=1024",
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="avatar",
        description="""Show a users avatar""",
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

    @commands.command(
        name="info",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        aliases=["i"],
        enabled=True,
        hidden=False,
    )
    async def info_cmd(self, ctx, person: discord.Member = None):
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

    @commands.hybrid_command(
        name="dog",
        description="""Get a random dog image!""",
        help="""What good bot doesn't have a dog command?""",
        brief="Get a random dog image",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 3.0, commands.BucketType.user)
    async def dog_cmd(self, ctx):
        """dog command"""
        dog = await self.bot.aiosession.get("https://dog.ceo/api/breeds/image/random")

        dog_image = (await dog.json()).get("message")
        embed = discord.Embed(color=style.get_color())
        embed.set_image(url=dog_image)
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="uptime",
        description="""Shows the bots uptime""",
        help="""Shows you the bots uptime""",
        brief="Shows you the bots uptime",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 30.0, commands.BucketType.channel)
    async def uptime_cmd(self, ctx):
        """
        Uptime Slash
        """
        resolved_full = discord.utils.format_dt(self.bot.start_time, "F")
        resolved_rel = discord.utils.format_dt(self.bot.start_time, "R")
        fmt = (
            f"I started at `{resolved_full}`, and have been up since: `{resolved_rel}`"
        )
        embed = discord.Embed(
            title=f"Benny Uptime",
            description=f"""{fmt}""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color(),
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="ping",
        description="""Check the bots current ping""",
        help="""Check the bots latency stats""",
        brief="Check the ping",
        aliases=[],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(2.0, 10.0, commands.BucketType.user)
    async def ping_cmd(self, ctx):
        """Ping command"""
        start = time.monotonic()
        embed = discord.Embed(
            title=f"Pinging...",
            description=f"""Checking Ping""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("grey")
        )
        msg = await ctx.send(embed=embed)
        end = time.monotonic()
        ping = round((end - start) * 1000, 2)
        bot_ping = round(self.bot.latency * 1000, 2)
        average_ping = (bot_ping + ping) / 2

        if average_ping >= 500:
            color = style.get_color("red")
        elif average_ping >= 250:
            color = style.get_color("orange")
        elif average_ping >= 100:
            color = style.get_color("yellow")
        else:
            color = style.get_color("green")

        ping_embed = discord.Embed(
            title="Pinging...", 
            description=f"""Overall Latency: {ping} ms
            Discord WebSocket Latency: {bot_ping}
            """,
            timestamp=discord.utils.utcnow(),
            color=color
        )
        await msg.edit(embed=ping_embed)

async def setup(bot):
    await bot.add_cog(Base(bot))
