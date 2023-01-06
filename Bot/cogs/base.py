import asyncio
import datetime
import itertools
import json
import platform
import time
import unicodedata
from typing import List

import discord
import discord.utils
import psutil
import pygit2
from discord.ext import commands
from gears import embed_creator, style, util
from motor.motor_asyncio import AsyncIOMotorClient


def get_size(_bytes: int, suffix: str = "B") -> str:
    """
    Return the correct data from bytes
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if _bytes < factor:
            return f"{_bytes:.2f}{unit}{suffix}"
        _bytes /= factor
    return None


class AvatarView(discord.ui.View):
    """
    Delete view to delete the message from the bot
    """

    @discord.ui.button(
        emoji=style.Emoji.REGULAR.cancel,
        label="Delete",
        style=discord.ButtonStyle.danger,
    )
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
            if afk_data.get("unix") + 3 < int(time.time()):
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


class SystemView(discord.ui.View):
    """
    System view with buttons to view all options
    """

    @discord.ui.button(style=discord.ButtonStyle.primary, label="Info", emoji="ℹ")
    async def info_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Send the info embed
        """
        uname = platform.uname()
        embed = discord.Embed(
            title="System Info - Info",
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
        embed.set_footer(text="Select one of the below options for more info")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary, label="CPU", emoji="🖥️")
    async def cpu_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Send the cpu embed and related
        """
        cpu_core_data = ""
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            cpu_core_data += f"""[Core {i + 1}]
= {percentage}% =\n"""

        embed = discord.Embed(
            title="System Info - CPU",
            description=f"""```asciidoc
[ Total Cores ]
= {psutil.cpu_count(logical=True)} =

[ CPU Usage Per Core ]
{cpu_core_data}
[ Total CPU Usage ]
= {psutil.cpu_percent()}% =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREY,
        )
        embed.set_footer(text="Select one of the below options for more info")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary, label="RAM", emoji="💾")
    async def ram_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Show ram related info
        """
        svmem = psutil.virtual_memory()
        embed = discord.Embed(
            title="System Info - Memory",
            description=f"""```asciidoc
[ Total ]
= {get_size(svmem.total)} =
[ Available ]
= {get_size(svmem.available)} =
[ Used ]
= {get_size(svmem.used)} =
[ Percentage Used ]
= {svmem.percent}% =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREY,
        )
        embed.set_footer(text="Select one of the below options for more info")
        await interaction.response.edit_message(embed=embed, view=self)


class RoleAllView(discord.ui.View):
    """
    A view to start giving roles to everyone
    """

    def __init__(
        self, ctx: commands.Context, members: List[discord.Member], role: discord.Role
    ) -> None:
        """
        Initialize the view
        """
        super().__init__()
        self.ctx = ctx
        self.members = members
        self.role = role

    @discord.ui.button(
        style=discord.ButtonStyle.green,
        label="Start",
        emoji=style.Emoji.REGULAR.check,
    )
    async def start_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Start giving roles to everyone
        """
        await self.start_giving_roles(interaction, self.role)

    @discord.ui.button(
        style=discord.ButtonStyle.danger,
        label="Cancel",
        emoji=style.Emoji.REGULAR.cancel,
    )
    async def cancel_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Cancel the view
        """
        await interaction.message.delete()
        await self.ctx.command.reset_cooldown(self.ctx)

    async def start_giving_roles(
        self, interaction: discord.Interaction, role: discord.Role
    ) -> None:
        """
        Start giving roles to everyone
        """
        embed = discord.Embed(
            title="Bulk Role Add - In Progress",
            description="""This message will edit itself when it is finished.""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.YELLOW,
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(
            "Starting to give roles to everyone...", ephemeral=True
        )

        for member in self.members:
            if role not in member.roles:
                await member.add_roles(role)
                await asyncio.sleep(1)

        embed = discord.Embed(
            title="Bulk Role Add - Finished",
            description="""Finished giving roles to everyone!""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        await interaction.message.edit(embed=embed)


class RoleRallView(discord.ui.View):
    """
    A view to start removing roles to everyone
    """

    def __init__(
        self, ctx: commands.Context, members: List[discord.Member], role: discord.Role
    ) -> None:
        """
        Initialize the view
        """
        super().__init__()
        self.ctx = ctx
        self.members = members
        self.role = role

    @discord.ui.button(
        style=discord.ButtonStyle.green,
        label="Start",
        emoji=style.Emoji.REGULAR.check,
    )
    async def start_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Start removing roles from everyone
        """
        await self.start_removing_roles(interaction, self.role)

    @discord.ui.button(
        style=discord.ButtonStyle.danger,
        label="Cancel",
        emoji=style.Emoji.REGULAR.cancel,
    )
    async def cancel_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Cancel the view
        """
        await interaction.message.delete()
        await self.ctx.command.reset_cooldown(self.ctx)

    async def start_removing_roles(
        self, interaction: discord.Interaction, role: discord.Role
    ) -> None:
        """
        Start giving roles to everyone
        """
        embed = discord.Embed(
            title="Bulk Role Remove - In Progress",
            description="""This message will edit itself when it is finished.""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.YELLOW,
        )
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(
            "Starting to remove roles from everyone...", ephemeral=True
        )

        for member in self.members:
            if role in member.roles:
                await member.remove_roles(role)
                await asyncio.sleep(1)

        embed = discord.Embed(
            title="Bulk Role Remove - Finished",
            description="""Finished removing roles from everyone!""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        await interaction.message.edit(embed=embed)


class Base(commands.Cog):
    """
    Basic commands that you would use with no specific category
    """

    COLOR = style.Color.AQUA
    ICON = "🧱"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init
        """
        self.bot = bot
        self.MemberConverter = commands.MemberConverter()
        self.RoleConverter = commands.RoleConverter()
        self.afk = AFKManager(bot)
        self.session = bot.sessions.get("base")

    def format_commit(self, commit: pygit2.Commit) -> str:
        """
        From rdanny
        """
        short, _, _ = commit.message.partition("\n")
        short_sha2 = commit.hex[0:8]
        commit_tz = datetime.timezone(
            datetime.timedelta(minutes=commit.commit_time_offset)
        )
        commit_time = datetime.datetime.fromtimestamp(commit.commit_time).astimezone(
            commit_tz
        )

        offset = discord.utils.format_dt(
            commit_time.astimezone(datetime.timezone.utc), "R"
        )
        return f"[`{short_sha2}`](https://github.com/Leg3ndary/Benny/commit/{commit.hex}) {short} ({offset})"

    def get_latest_commits(self, count) -> str:
        """
        Stole this from rdanny because I'm lazy
        """
        repo = pygit2.Repository(".git")
        commits = list(
            itertools.islice(
                repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL), count
            )
        )
        return "\n".join(self.format_commit(c) for c in commits)

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
        embed.add_field(name="Version", value=self.get_latest_commits(5))
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
        brief="""Show a users avatar""",
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

    @commands.command(
        name="uptime",
        description="""Shows the bots uptime so that users can judge how long it has been online.""",
        help="""Shows you the bots uptime""",
        brief="Shows you the bots uptime",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.channel)
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
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="ping",
        description="""Check the bots current ping and latency""",
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
        embed.set_footer(
            text="Please note that this will be much slower when you use slash commands"
        )
        msg = await ctx.reply(embed=embed)
        end = time.monotonic()
        ping = round((end - start), 2)
        bot_ping = round(self.bot.latency, 2)
        average_ping = (bot_ping + ping) / 2

        if average_ping >= 3:
            color = style.Color.RED
        elif average_ping >= 2:
            color = style.Color.ORANGE
        elif average_ping >= 1:
            color = style.Color.YELLOW
        else:
            color = style.Color.GREEN

        ping_embed = discord.Embed(
            title="Pinging...",
            description=f"""**Overall Latency:** `{ping}`s
            **Discord WebSocket Latency:** `{bot_ping}`s""",
            timestamp=discord.utils.utcnow(),
            color=color,
        )
        ping_embed.set_footer(
            text="Please note that this will be much slower when you use slash commands"
        )
        await msg.edit(embed=ping_embed)

    @commands.command(
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
        uname = platform.uname()
        svmem = psutil.virtual_memory()
        embed = discord.Embed(
            title="System Info",
            description=f"""```asciidoc
[ System ]
= {uname.system} =
[ Total Cores ]
= {psutil.cpu_count(logical=True)} =
[ Total Used vs Total Free]
= {get_size(svmem.used)}/{get_size(svmem.total)} = 
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREY,
        )
        embed.set_footer(text="Select one of the below options for more info")
        await ctx.reply(embed=embed, view=SystemView())

    @commands.command(
        name="files",
        description="""View all our files and lines because I think it's cool""",
        help="""Recursively looks for all files and how many lines they have""",
        brief="View file info",
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
            text=f"{len(self.bot.file_list)} files listed.",
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_group(
        name="afk",
        description="""All AFK related commands""",
        help="""All AFK related commands""",
        brief="AFK commands",
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
        description="""Set an AFK status for mentions""",
        help="""Set a custom AFK message""",
        brief="Set a custom AFK message",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
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
        if not msg.author.bot:
            await self.afk.manage_afk(msg)

    @commands.hybrid_command(
        name="version",
        description="""Check the current version of the bot""",
        help="""Check the current version of the bot""",
        brief="Check the current version of the bot",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.channel)
    async def version_cmd(self, ctx: commands.Context) -> None:
        """
        Version command
        """
        repo = pygit2.Repository(".git")

        commits = self.get_latest_commits(8)

        embed = discord.Embed(
            title=f"Current Version: {repo.head.target.hex[0:8]}",
            description=f"""{commits}""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="invite",
        description="""Invite the bot to your server""",
        help="""Invite the bot to your server""",
        brief="Invite the bot to your server",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.channel)
    async def invite_cmd(self, ctx: commands.Context) -> None:
        """
        Invite command
        """
        embed = discord.Embed(
            title="Invite Me",
            description=f"""[Invite](https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=1636352650487&scope=applications.commands%20bot) me to your server!""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="custom_embed",
        description="""Create a custom embed""",
        help="""Create a custom embed""",
        brief="Create a custom embed",
        aliases=["cembed", "ce"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def custom_embed_cmd(self, ctx: commands.Context) -> None:
        """
        Create a custom embed
        """
        embed = discord.Embed(
            title="Embed Creator",
            description="Create an embed with this view!",
            timestamp=discord.utils.utcnow(),
        )
        view = embed_creator.CustomEmbedView(ctx, embed)
        await ctx.reply(embed=embed, view=view)

    @commands.hybrid_group(
        name="role",
        description="""Role related commands""",
        help="""Role related commands""",
        brief="Role related commands",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def role_group(self, ctx: commands.Context) -> None:
        """
        Role related commands
        """
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @role_group.command(
        name="add",
        description="""Add a role to a member""",
        help="""Add a role to a member""",
        brief="Add a role to a member",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def role_add_cmd(
        self, ctx: commands.Context, member: discord.Member, role: discord.Role
    ) -> None:
        """
        Add a role to a member
        """
        if ctx.author.top_role < member.top_role:
            raise commands.BadArgument(
                f"You cannot add {role.mention} to {member.mention} as their highest role is higher than your highest role ({member.top_role.mention})."
            )
        if role > member.top_role:
            raise commands.BadArgument(
                f"You cannot add {role.mention} to {member.mention} as it's higher than their top role ({member.top_role.mention})."
            )

        await member.add_roles(role)
        embed = discord.Embed(
            title="Role Added",
            description=f"""Added {role.mention} to {member.mention}""",
            timestamp=discord.utils.utcnow(),
            color=role.color,
        )
        embed.set_footer(text=f"Role ID: {role.id}")
        await ctx.reply(embed=embed)

    @role_group.command(
        name="remove",
        description="""Remove a role from a member""",
        help="""Remove a role from a member""",
        brief="Remove a role from a member",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def role_remove_cmd(
        self, ctx: commands.Context, member: discord.Member, role: discord.Role
    ) -> None:
        """
        Remove a role from a member
        """
        if ctx.author.top_role < member.top_role:
            raise commands.BadArgument(
                f"You cannot remove {role.mention} from {member.mention} as their highest role ({member.top_role.mention}) is higher than your highest role ({ctx.author.top_role.mention})."
            )
        if role == member.top_role:
            raise commands.BadArgument(
                f"You cannot remove {role.mention} from {member.mention} as it's their highest role ({member.top_role.mention})."
            )

        await member.remove_roles(role)
        embed = discord.Embed(
            title="Role Removed",
            description=f"""Removed {role.mention} from {member.mention}""",
            timestamp=discord.utils.utcnow(),
            color=role.color,
        )
        embed.set_footer(text=f"Role ID: {role.id}")
        await ctx.reply(embed=embed)

    @role_group.command(
        name="custom",
        description="""Custom add/remove roles to a member""",
        help="""Custom add/remove roles to a member, use +role and -role to add and remove roles respectively, use ! to invert them, if they have the role, it will be removed, if they don't have it, it will be added.""",
        brief="Custom add/remove roles to a member",
        aliases=["c"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def role_custom_command(
        self, ctx: commands.Context, member: discord.Member, *, role_str: str
    ) -> None:
        """
        Add roles to a member based on a string customly, does that make sense?
        """
        add = []
        remove = []

        for role in role_str.split():
            if role.startswith("+"):
                add.append(await self.RoleConverter.convert(ctx, role[1:]))
            elif role.startswith("-"):
                remove.append(await self.RoleConverter.convert(ctx, role[1:]))
            elif role.startswith("!"):
                temp = await self.RoleConverter.convert(ctx, role[1:])
                if temp in member.roles:
                    remove.append(temp)
                else:
                    add.append(temp)

        if ctx.author.top_role < member.top_role:
            raise commands.BadArgument(
                f"You cannot manage these roles from {member.mention} as their highest role ({member.top_role.mention}) is higher than your highest role ({ctx.author.top_role.mention})."
            )

        for role in add:
            if role > member.top_role:
                raise commands.BadArgument(
                    f"You cannot add {role.mention} to {member.mention} as it's higher than their top role ({member.top_role.mention})."
                )
        for role in remove:
            if role == member.top_role:
                raise commands.BadArgument(
                    f"You cannot remove {role.mention} from {member.mention} as it's their highest role ({member.top_role.mention})."
                )

        await member.add_roles(*add)
        await member.remove_roles(*remove)

        embed = discord.Embed(
            title="Role Custom",
            timestamp=discord.utils.utcnow(),
            color=role.color,
        )
        embed.add_field(
            name="Added",
            value="\n".join([role.mention for role in add]) or "None",
        )
        embed.add_field(
            name="Removed",
            value="\n".join([role.mention for role in remove]) or "None",
        )
        embed.set_footer(text=f"Role ID: {role.id}")
        await ctx.reply(embed=embed)

    @role_group.command(
        name="all",
        description="""Give everyone a role""",
        help="""Give everyone a role""",
        brief="Give everyone a role",
        aliases=["bulk"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 3600.0, commands.BucketType.guild)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def role_all_cmd(self, ctx: commands.Context, *, role: discord.Role) -> None:
        """
        Add roles to all members that don't already have the role
        """
        await ctx.defer()
        members = [member for member in ctx.guild.members if role not in member.roles]
        embed = discord.Embed(
            title="Bulk Role Add",
            description=f"""This will add {role.mention} to {len(members)} different members, are you sure you want to do this?
            
            This will take {len(members)} seconds to complete.
            
            You will not be able to cancel this action.""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        await ctx.send(embed=embed, view=RoleAllView(ctx, members, role))

    @role_group.command(
        name="rall",
        description="""Remove a role from everyone""",
        help="""Remove a role from everyone""",
        brief="Remove a role from everyone",
        aliases=["removeall"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 3600.0, commands.BucketType.guild)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def role_rall_cmd(self, ctx: commands.Context, *, role: discord.Role) -> None:
        """
        Remove roles from all members that have the role
        """
        await ctx.defer()
        members = [member for member in ctx.guild.members if role in member.roles]
        embed = discord.Embed(
            title="Bulk Role Remove",
            description=f"""This will remove {role.mention} from {len(members)} different members, are you sure you want to do this?
            
            This will take `{len(members)}` seconds to complete.
            
            **You will not be able to cancel this action.**""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        await ctx.send(embed=embed, view=RoleRallView(ctx, members, role))


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Base(bot))
