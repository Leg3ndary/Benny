import io
import json
import platform
import time
import unicodedata

import aiohttp
import discord
import discord.utils
import PIL as pil
import psutil
import pytesseract
from discord.ext import commands
from gears import style
from motor.motor_asyncio import AsyncIOMotorClient


class AvatarView(discord.ui.View):
    """
    Delete view to delete the message from the bot
    """

    @discord.ui.button(emoji=style.Emoji.ID.cancel, label="Delete", style=discord.ButtonStyle.danger)
    async def button_callback(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Delete the message
        """
        await interaction.delete_original_message()


class AFKManager:
    """
    Manage afk sessions and related data
    """

    pcc = None

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init the manager
        """
        self.bot = bot
        self.pcc = bot.pcc
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
            await message.reply(embed=embed)

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

    __slots__ = ("bot", "loop")

    def __init__(self, bot: commands.Bot) -> None:
        """
        construct the image reader
        """
        self.bot = bot
        self.loop = bot.loop

        if not bot.PLATFORM == "linux":
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
    """
    Basic commands that you would use with no specific category
    """

    COLOR = style.Color.AQUA
    ICON = ":bricks:"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init
        """
        self.bot = bot
        self.MemberConverter = commands.MemberConverter()
        self.afk = AFKManager(bot)
        self.session = bot.sessions.get("base")
        self.imgr = IMGReader(bot)

    def get_size(self, _bytes: int, suffix: str = "B") -> str:
        """
        Return the correct data from bytes
        """
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if _bytes < factor:
                return f"{_bytes:.2f}{unit}{suffix}"
            _bytes /= factor
        return None

    @commands.command(
        name="about",
        description="""About the bot, why I built it, what it can do, what I plan to do with it later on.""",
        help="""Shows information about the bot""",
        brief="About the bot",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 5.0, commands.BucketType.channel)
    async def about_cmd(self, ctx: commands.Context) -> None:
        """
        About command for the bot, just tells you a little bit about the bot
        """
        embed = discord.Embed(
            title="About the Bot",
            description="""A Bot I've made for fun, friends and learning python.
            The bot also does a lot of odd things I feel I may need such as reading text off images, playing music, and stealing sheetmusic, lol.
            Hope you enjoy""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        avatar = "https://cdn.discordapp.com/avatars/360061101477724170/a_6f4c033794b69ac35ce7b352ef7808bb.gif?size=1024"
        embed.set_footer(
            text="_Leg3ndary#0001",
            icon_url=avatar,
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="avatar",
        description="""Show a users avatar""",
        help="""Show a users avatar in a nice clean embed.""",
        brief="""Short help text""",
        aliases=["av", "pfp"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 5.0, commands.BucketType.user)
    async def avatar_cmd(
        self, ctx: commands.Context, *, user: discord.Member = None
    ) -> None:
        """
        Show a users avatar
        """
        if not user:
            user = ctx.author

        embed = discord.Embed(
            title=user.display_name, timestamp=discord.utils.utcnow(), color=user.color
        )
        embed.set_image(url=user.avatar.url)
        await ctx.reply(embed=embed, view=AvatarView())

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
            inline=False
        )
        embed.add_field(
            name="Joined At",
            value=discord.utils.format_dt(member.joined_at, "F"),
            inline=False
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
            url=member.display_avatar.url if member.display_avatar else member.avatar.url
        )
        await ctx.reply(embed=embed)

    # Make a permissions command along with a more complicated info view for above

    @commands.command(
        name="charinfo",
        aliases=["ci", "char"],
        description="""Tells you about a characters info an its unicode representations""",
        help="""Tells you about a characters info an its unicode representations""",
        brief="Tell you about a characters info",
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 5.0, commands.BucketType.user)
    async def charinfo_cmd(self, ctx: commands.Context, *, characters: str) -> None:
        """
        Gives you the character info of whatever you input
        """
        def to_string(char: str) -> str:
            digit = f"{ord(char):x}"
            name = unicodedata.name(char, "Name not found.")
            return f"`\\U{digit:>08} - {char}` [{name}](http://www.fileformat.info/info/unicode/char/{digit})"

        embed = discord.Embed(
            title="Charinfo",
            description="\n".join(map(to_string, characters)),
            timestamp=discord.utils.utcnow(),
            color=style.Color.YELLOW,
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="dog",
        description="""Get a random dog image!""",
        help="""What good bot doesn't have a dog command?""",
        brief="Get a random dog image",
        aliases=["doggo"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 5.0, commands.BucketType.channel)
    async def dog_cmd(self, ctx: commands.Context) -> None:
        """
        Dog command
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
    @commands.cooldown(1.0, 15.0, commands.BucketType.channel)
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
        aliases=["pong"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.channel)
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

    @commands.group(
        name="system",
        description="""Systeminfo group""",
        help="""Systeminfo group""",
        brief="Systeminfo group",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 5.0, commands.BucketType.user)
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
    async def system_info_cmd(self, ctx: commands.Context) -> None:
        """
        Showing full system information
        """
        uname = platform.uname()
        embed = discord.Embed(
            title="System Information",
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
            color=style.Color.GREY,
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
    @commands.cooldown(1.0, 10.0, commands.BucketType.channel)
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
        embed.set_footer(
            text=f"{len(self.bot.file_list)} files listed, value is lines to chars",
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
    @commands.guild_only()
    async def afk_group(self, ctx: commands.Context) -> None:
        """
        Afk hybrid_group
        """
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @afk_group.command(
        name="set",
        description="""Set your afk""",
        help="""Set your afk""",
        brief="Set your afk",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    async def afk_set_cmd(self, ctx: commands.Context, *, message: str) -> None:
        """
        Set your afk
        """
        await self.afk.set_afk(ctx, message)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message) -> None:
        """
        On a message, check if that user is either pinging an afk user or is an afk user with an
        active afk
        """
        await self.afk.manage_afk(msg)

    @commands.hybrid_command(
        name="imgread",
        description="""Read text off an image""",
        help="""Read text off an image""",
        brief="Read text off an image",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 8.0, commands.BucketType.user)
    async def imgread_cmd(self, ctx: commands.Context, url: str = None) -> None:
        """
        Use pytesseract to read stuff yay.
        """
        if url:
            async with self.session as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(url, timeout=timeout) as response:
                    image_bytes = await response.read()

        elif ctx.message.attachments:
            image_bytes = await ctx.message.attachments[0].read()

        else:
            raise commands.BadArgument("Please provide an image or url to read.")

        text = await self.imgr.read_img(image_bytes)
        if len(text) > 2000:
            n = 2000
            send_list = [text[i : i + n] for i in range(0, len(text), n)]

            for item in send_list:
                await ctx.send(item)
        await ctx.send(text)


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Base(bot))
