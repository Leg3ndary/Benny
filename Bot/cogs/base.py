import io
import json
import platform
import time
import unicodedata

import discord
import discord.utils
import PIL as pil
import psutil
import pytesseract
from discord.ext import commands
from gears import cviews, style
from motor.motor_asyncio import AsyncIOMotorClient


class AFKManager:
    """
    Manage afk sessions and related data
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init the manager
        """
        self.bot = bot
        mongo_uri = (
            self.bot.config.get("Mongo")
            .get("URL")
            .replace("<Username>", self.bot.config.get("Mongo").get("User"))
            .replace("<Password>", self.bot.config.get("Mongo").get("Pass"))
        )
        self.db = AsyncIOMotorClient(mongo_uri)["AFK"]

    async def set_afk(self, ctx: commands.Context, message: str) -> None:
        """
        Set an afk for a user in a certain guild
        """
        query = {"_id": str(ctx.author.id)}
        afk_doc = {
            "_id": str(ctx.author.id),
            "message": message,
            "unix": int(time.time()),
        }
        await self.db[str(ctx.message.guild.id)].replace_one(query, afk_doc, True)
        embed = discord.Embed(
            title="Set AFK",
            description=f""">>> {message}""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        await ctx.send(embed=embed)

    async def del_afk(self, guild: int, user: int) -> None:
        """
        Delete an afk from the db, usually called when a user has sent a message showing that they
        aren't actually afk
        """
        query = {"_id": str(user)}
        await self.db[str(guild)].delete_one(query)

    async def manage_afk(self, message: discord.Message) -> None:
        """
        Manage an afk when it gets sent here, first check if its a message from a user
        """
        query = {"_id": str(message.author.id)}
        afk_data = await self.db[str(message.guild.id)].find_one(query)
        if afk_data:
            await self.del_afk(message.guild.id, message.author.id)
            embed = discord.Embed(
                title="Removed AFK",
                description=f"""Welcome back {message.author.mention}!
                
                You've been afk since <t:{afk_data["unix"]}:R>""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.PINK,
            )
            await message.channel.send(embed=embed)

        for mention in message.mentions[:3]:
            if not message.author.id == mention.id:
                query = {"_id": str(mention.id)}
                afk_data = await self.db[str(message.guild.id)].find_one(query)
                username = (
                    self.bot.get_user(mention.id)
                    or (await self.bot.fetch_user(mention.id))
                ).name
                if afk_data:
                    embed = discord.Embed(
                        title=f"{username} is AFK",
                        description=afk_data["message"],
                        timestamp=discord.utils.utcnow(),
                        color=style.Color.PINK,
                    )
                    await message.channel.send(embed=embed)


class IMGReader:
    """
    Read images
    """

    def __init__(self, bot: commands.Bot) -> None:
        """Init"""
        self.bot = bot
        self.loop = bot.loop

        if not bot.PLATFORM.lower() == "linux":
            pytesseract.pytesseract.tesseract_cmd = (
                "C:/Program Files/Tesseract-OCR/tesseract.exe"
            )

    async def read_img(self, image_bytes: bytes) -> str:
        """
        Read an image and return the text in it

        Parameters
        ----------
        image_bytes: bytes
            Image bytes

        Returns
        -------
        str
            The actual text found
        """

        img = await self.loop.run_in_executor(
            None, pil.Image.open, io.BytesIO(image_bytes)
        )
        text = await self.loop.run_in_executor(
            None, pytesseract.pytesseract.image_to_string, img
        )

        return text


class Base(commands.Cog):
    """Basic commands that you would use with no specific category"""

    def __init__(self, bot: commands.Bot) -> None:
        """Init"""
        self.bot = bot
        self.MemberConverter = commands.MemberConverter()
        self.afk = AFKManager(bot)
        self.session = bot.sessions.get("base")
        self.imgr = IMGReader(bot)

    def get_size(self, _bytes, suffix="B") -> str:
        """Return the correct data from bytes"""
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if _bytes < factor:
                return f"{_bytes:.2f}{unit}{suffix}"
            _bytes /= factor

    @commands.command(
        name="about",
        description="""About command for the bot, tells you a bit about the bot""",
        help="""About the bot, why I built it, what it can and is going to do""",
        brief="About the bot",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.channel)
    async def about_cmd(self, ctx: commands.Context) -> None:
        """
        About command for the bot, just tells you a little bit about the bot
        """
        embed = discord.Embed(
            title="About the Bot",
            description="""A Bot I've made for fun, friends and learning python.""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        avatar = "https://cdn.discordapp.com/avatars/360061101477724170/798fd1d22b6c219236ad97be44aa425d.png?size=1024"
        embed.set_footer(
            text="_Leg3ndary#5759",
            icon_url=avatar,
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
    async def avatar_cmd(
        self, ctx: commands.Context, *, user: discord.Member = None
    ) -> None:
        """
        Show a users avatar
        """
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
        description="""View a users info""",
        help="""View some info about a user""",
        brief="""View some info about a user""",
        aliases=["i"],
        enabled=True,
        hidden=False,
    )
    async def info_cmd(
        self, ctx: commands.Context, person: discord.Member = None
    ) -> None:
        """
        View an users info
        """
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
            {person.system}
            Not Completed.""",
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
    async def charinfo(self, ctx: commands.Context, *, characters: str) -> None:
        """
        Gives you the character info of whatever you input
        """

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
    async def dog_cmd(self, ctx: commands.Context) -> None:
        """
        dog command
        """
        dog = await self.session.get("https://dog.ceo/api/breeds/image/random")

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
    async def uptime_cmd(self, ctx: commands.Context) -> None:
        """
        Uptime command to show the bots uptime
        """
        resolved_full = discord.utils.format_dt(self.bot.START_TIME, "F")
        resolved_rel = discord.utils.format_dt(self.bot.START_TIME, "R")
        fmt = f"""Started at {resolved_full}
Total Uptime: {resolved_rel}"""
        embed = discord.Embed(
            title=f"{self.bot.user.name} Uptime",
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
    async def ping_cmd(self, ctx: commands.Context) -> None:
        """
        Ping command
        """
        start = time.monotonic()
        embed = discord.Embed(
            title="Pinging...",
            description="""Checking Ping""",
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
    async def system_group(self, ctx: commands.Context) -> None:
        """
        Actual system info
        """
        if not ctx.invoked_subcommand:
            embed = discord.Embed(
                title="System Info",
                description="""**Options:**
```asciidoc
[ info ]
[ boot ]
[ cpu ]
[ memory ]
[ disk ]
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.random(),
            )
            await ctx.send(embed=embed)

    @system_group.command(
        name="info",
        description="""Show overall information about our vps""",
        help="""Show information about vps""",
        brief="Show information",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def system_info_cmd(self, ctx: commands.Context) -> None:
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
        await ctx.send(embed=embed)

    @system_group.command(
        name="cpu",
        description="""Show overall cpu cores and related information""",
        help="""Show cpu information""",
        brief="Show cpu information",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def system_cpu_cmd(self, ctx: commands.Context) -> None:
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
        await ctx.send(embed=embed)

    @system_group.command(
        name="memory",
        description="""Show total memory and free percentage""",
        help="""Show total memory and percentages""",
        brief="Show memory information",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def system_memory_cmd(self, ctx: commands.Context) -> None:
        """
        Showing our memory information
        """
        svmem = psutil.virtual_memory()
        embed = discord.Embed(
            title="================ Memory Information ================",
            description=f"""```asciidoc
[ Total ]
= {self.get_size(svmem.total)} = 
[ Available ]
= {self.get_size(svmem.available)} =
[ Used ]
= {self.get_size(svmem.used)} =
[ Percentage ]
= {svmem.percent}% =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.random(),
        )
        await ctx.send(embed=embed)

    @system_group.command(
        name="disk",
        description="""Show overall disk space and partitions""",
        help="""Show disk space, hidden because eh""",
        brief="Show disk space",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def system_disk_cmd(self, ctx: commands.Context) -> None:
        """
        Showing our disk information
        """
        partitions = psutil.disk_partitions()
        disk_io = psutil.disk_io_counters()
        embed = discord.Embed(
            title="================= Disk Information =================",
            description=f"""```asciidoc
[ Total Read ]
= {self.get_size(disk_io.read_bytes)} = 
[ Total Write ]
= {self.get_size(disk_io.write_bytes)} =
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
= {self.get_size(partition_usage.total)} =
[ Used ]
= {self.get_size(partition_usage.used)} =
[ Free ]
= {self.get_size(partition_usage.free)} =
[ Percentage ]
= {partition_usage.percent}% =
```""",
                inline=False,
            )
        await ctx.send(embed=embed)

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
    async def files_cmd(self, ctx: commands.Context) -> None:
        """
        Send our stuff
        """
        embed = discord.Embed(
            title="File Lines",
            description=f"""```json
{json.dumps(self.bot.file_list, indent=4, sort_keys=True)}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        await ctx.send(embed=embed)

    @commands.hybrid_group(
        name="afk",
        description="""AFK Command Group""",
        help="""Afk Command Group""",
        brief="AFK command group",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def afk_group(self, ctx: commands.Context) -> None:
        """Afk hybrid_group"""

    @afk_group.command(
        name="set",
        description="""Set your afk""",
        help="""Set your afk""",
        brief="Set your afk",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    @commands.guild_only()
    async def afk_set_cmd(self, ctx: commands.Context, *, message: str) -> None:
        """Set your afk"""
        await self.afk.set_afk(ctx, message)

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        """
        On a message, check if that user is either pinging an afk user or is an afk user with an 
        active afk
        """
        await self.afk.manage_afk(message)

    @commands.command(
        name="imgread",
        description="""Description of command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def my_command(self, ctx: commands.Context, url: str = None) -> None:
        """Command description"""
        if url:
            async with self.session as session:
                async with session.get(url) as response:
                    image_bytes = await response.read()

        else:
            image_bytes = await ctx.message.attachments[0].read()

        text = await self.imgr.read_img(image_bytes)
        await ctx.send(text)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Base(bot))
