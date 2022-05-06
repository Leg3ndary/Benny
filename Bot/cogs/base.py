import time

import discord
import discord.utils
import json
import platform
import psutil
import random
import unicodedata
from discord.ext import commands
from gears import cviews, style


"""@commands.dynamic_cooldown(custom_cooldown, commands.BucketType.user)
async def ping(ctx):
    await ctx.send("pong")"""


def get_size(bytes, suffix="B"):
    """Return the correct data from bytes"""
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


class Base(commands.Cog):
    """Basic commands that you would use with no specific category"""

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
            color=style.Color.AQUA,
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
            color=style.Color.random(),
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
        embed = discord.Embed(color=style.Color.random())
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
        fmt = f"""Started at {resolved_full}
Total Uptime: {resolved_rel}"""
        embed = discord.Embed(
            title=f"Benny Uptime",
            description=f"""{fmt}""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.random(),
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="ping",
        description="""Check the bots current ping""",
        help="""Check the bots latency stats""",
        brief="Check the ping",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 10.0, commands.BucketType.user)
    async def ping_cmd(self, ctx):
        """Ping command"""
        start = time.monotonic()
        embed = discord.Embed(
            title=f"Pinging...",
            description=f"""Checking Ping""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREY,
        )
        msg = await ctx.send(embed=embed)
        end = time.monotonic()
        ping = round((end - start) * 1000, 2)
        bot_ping = round(self.bot.latency * 1000, 2)
        average_ping = (bot_ping + ping) / 2

        if average_ping >= 500:
            color = style.Color.RED
        elif average_ping >= 250:
            color = style.Color.ORANGE
        elif average_ping >= 100:
            color = style.Color.YELLOW
        else:
            color = style.Color.GREEN

        ping_embed = discord.Embed(
            title="Pinging...",
            description=f"""Overall Latency: {ping} ms
            Discord WebSocket Latency: {bot_ping}
            """,
            timestamp=discord.utils.utcnow(),
            color=color,
        )
        await msg.edit(embed=ping_embed)

    @commands.group()
    @commands.cooldown(3.0, 7.0, commands.BucketType.user)
    async def system(self, ctx):
        """Actual system info"""
        if not ctx.invoked_subcommand:
            options = ["info", "boot", "cpu", "memory", "disk"]
            embed = discord.Embed(
                title="Tenshi PC Info",
                description=f"""**Options:**
```asciidoc
[ info ]
[ boot ]
[ cpu ]
[ memory ]
[ disk ]
```
                Example:
```fix
system {random.choice(options)}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.random(),
            )
            return await ctx.send(embed=embed)

    @system.command(
        name="info",
        description="""Show overall information about our vps""",
        help="""Show information about vps""",
        brief="Show information",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def info_cmd(self, ctx):
        """Showing full system information"""
        uname = platform.uname()
        embed = discord.Embed(
            title="================ System Information ================",
            description=f"""```asciidoc
[ System ]
= {uname.system} =
[ Node Name ]
= {uname.node} =
[ Release ]
= {uname.release} =
[ Version ]
= {uname.version} =
[ Machine ]
= {uname.machine} =
[ Processor ]
= {uname.processor} =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.random(),
        )
        return await ctx.send(embed=embed)

    @system.command(
        name="cpu",
        description="""Show overall cpu cores and related information""",
        help="""Show cpu information""",
        brief="Show cpu information",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def cpu_cmd(self, ctx):
        """
        Showing our cpu information

        cpufreq = psutil.cpu_freq()
        [ Max Frequency ]
        = {cpufreq.max:.2f}Mhz =
        [ Min Frequency ]
        = {cpufreq.min:.2f}Mhz =
        [ Current Frequency ]
        = {cpufreq.current:.2f}Mhz =
        """

        cpu_core_data = ""
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            cpu_core_data = f"""{cpu_core_data}[Core {i}]
= {percentage}% =\n"""

        embed = discord.Embed(
            title="================= CPU Information =================",
            description=f"""```asciidoc
[ Physical Cores]
= {psutil.cpu_count(logical=False)} =
[ Total Cores ]
= {psutil.cpu_count(logical=True)} =
[ CPU Usage Per Core ]
{cpu_core_data}
[ Total CPU Usage ]
= {psutil.cpu_percent()}% =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.random(),
        )
        return await ctx.send(embed=embed)

    @system.command(
        name="memory",
        description="""Show total memory and free percentage""",
        help="""Show total memory and percentages""",
        brief="Show memory information",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def memory_cmd(self, ctx):
        """
        Showing our memory information
        """
        svmem = psutil.virtual_memory()
        embed = discord.Embed(
            title="================ Memory Information ================",
            description=f"""```asciidoc
[ Total ]
= {get_size(svmem.total)} = 
[ Available ]
= {get_size(svmem.available)} =
[ Used ]
= {get_size(svmem.used)} =
[ Percentage ]
= {svmem.percent}% =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.random(),
        )
        return await ctx.send(embed=embed)

    @system.command(
        name="disk",
        description="""Show overall disk space and partitions""",
        help="""Show disk space, hidden because eh""",
        brief="Show disk space",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def disk_cmd(self, ctx):
        """
        Showing our disk information
        """
        partitions = psutil.disk_partitions()
        disk_io = psutil.disk_io_counters()
        embed = discord.Embed(
            title="================= Disk Information =================",
            description=f"""```asciidoc
[ Total Read ]
= {get_size(disk_io.read_bytes)} = 
[ Total Write ]
= {get_size(disk_io.write_bytes)} =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.random(),
        )
        for partition in partitions:
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                # Will allow even if some disks aren't ready to be loaded
                continue
            embed.add_field(
                name=f"{partition.device}",
                value=f"""```asciidoc
[ Mountpoint ]
= {partition.mountpoint} = 
[ File System Type ]
= {partition.fstype} =
[ Total Size ]
= {get_size(partition_usage.total)} =
[ Used ]
= {get_size(partition_usage.used)} =
[ Free ]
= {get_size(partition_usage.free)} =
[ Percentage ]
= {partition_usage.percent}% =
```""",
                inline=False,
            )
        return await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="files",
        description="""View all our files and lines because I think it's cool""",
        help="""Recursively looks for all files and how many lines they have""",
        brief="View file lines",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 7.0, commands.BucketType.user)
    async def files_cmd(self, ctx):
        """
        Send our stuff
        """
        embed = discord.Embed(
            title=f"File Lines",
            description=f"""```json
{json.dumps(self.bot.file_list, indent=4, sort_keys=True)}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Base(bot))
