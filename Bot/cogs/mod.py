import asyncio
import datetime
import time
from sqlite3 import Row as sqlRow
from typing import Optional

import asqlite
import discord
import discord.utils
import parsedatetime
from discord.ext import commands, tasks
from gears import style


class Infraction:
    """
    Class for your standard infraction
    """

    __slots__ = (
        "case_id",
        "guild",
        "mod",
        "offender",
        "time",
        "reason",
        "active",
        "expires",
    )

    def __init__(self, row: sqlRow) -> None:
        """
        Construct the infraction
        """
        self.case_id: str = row[0]
        self.guild: str = row[1]
        self.mod: str = row[2]
        self.offender: str = row[3]
        self.time: int = row[4]
        self.reason: Optional[str] = row[5]
        if len(row) == 7:
            self.active: bool = row[6]
        else:
            self.expires: int = row[6]
            self.active: bool = row[7]


class ModerationManager:
    """
    Class for managing moderation actions
    """

    def __init__(self, bot: commands.Bot, db: asqlite.Connection) -> None:
        """
        Init the bot
        """
        self.bot = bot
        self.calendar = parsedatetime.Calendar()
        self.db = db
        self.count_db = bot.mongo["Mod"]
        self.infraction_tasks = {}

    async def get_count(self, guild: str) -> int:
        """
        Get the current moderation counter
        """
        guild_coll = self.count_db["Counts"]
        query = {"_id": str(guild)}
        doc = await guild_coll.find_one(query)

        if not doc:
            doc = {"_id": str(guild), "count": 1}
            await guild_coll.insert_one(doc)
        count = doc.get("count")
        await guild_coll.update_one(query, {"$set": {"count": count + 1}})

        return count

    async def pull_time(self, string: str) -> int:
        """
        Pull the time from a string
        """
        (
            time_struct,
            parse_status,
        ) = self.calendar.parse(  # pylint: disable=unused-variable
            string
        )
        """if parse_status == 0:
            raise commands.BadArgument("Time not found")"""
        return int(datetime.datetime(*time_struct[:6]).timestamp())

    async def warn(
        self,
        ctx: commands.Context,
        mod: discord.Member,
        member: discord.Member,
        reason: str,
    ) -> None:
        """
        Warn a member
        """
        current_time = int(time.time())

        await self.db.execute(
            """INSERT INTO warns VALUES(?, ?, ?, ?, ?, ?);""",
            (
                await self.get_count(str(ctx.guild.id)),
                str(ctx.guild.id),
                str(mod.id),
                str(member.id),
                current_time,
                reason,
            ),
        )
        await self.db.commit()

        embed = discord.Embed(
            title=f"Warned {member.name}#{member.discriminator}",
            description=reason,
            timestamp=discord.utils.utcnow(),
            color=style.Color.YELLOW,
        )
        embed.set_footer(
            text=f"Warned by {mod.name}#{mod.discriminator}",
            icon_url=mod.avatar.url,
        )
        await ctx.send(embed=embed)

    async def mute(
        self,
        ctx: commands.Context,
        mod: discord.Member,
        member: discord.Member,
        reason: str,
    ) -> None:
        """
        Mute a member
        """
        future_time = await self.pull_time(reason)
        current_time = int(time.time())

        await self.db.execute(
            """INSERT INTO mutes VALUES(?, ?, ?, ?, ?, ?, ?);""",
            (
                await self.get_count(str(ctx.guild.id)),
                str(ctx.guild.id),
                str(mod.id),
                str(member.id),
                current_time,
                reason,
                future_time if future_time >= current_time else None,
            ),
        )
        reason = (
            f"{reason}\n\nExpires in <t:{future_time}:R>"
            if future_time >= current_time
            else reason
        )

        await self.db.commit()

        embed = discord.Embed(
            title=f"Muted {member.name}#{member.discriminator}",
            description=reason,
            timestamp=discord.utils.utcnow(),
            color=style.Color.RED,
        )
        embed.set_footer(
            text=f"Muted by {mod.name}#{mod.discriminator}",
            icon_url=mod.avatar.url,
        )
        await ctx.send(embed=embed)

    async def ban(
        self,
        ctx: commands.Context,
        mod: discord.Member,
        member: discord.Member,
        reason: Optional[str],
    ) -> None:
        """
        bans a member
        """
        future_time = await self.pull_time(reason)
        current_time = int(time.time())

        await self.db.execute(
            """INSERT INTO bans VALUES(?, ?, ?, ?, ?, ?, ?);""",
            (
                await self.get_count(str(ctx.guild.id)),
                str(ctx.guild.id),
                str(mod.id),
                str(member.id),
                current_time,
                reason,
                future_time if future_time >= current_time else None,
            ),
        )
        reason = (
            f"{reason}\n\nExpires in <t:{future_time}:R>"
            if future_time >= current_time
            else reason
        )

        await self.db.commit()

        reason = f"Banned by {ctx.author}: " + reason if reason else "No Reason"
        await member.ban(reason=reason)

        embed = discord.Embed(
            title=f"Banned {member.name}#{member.discriminator}",
            description=reason,
            timestamp=discord.utils.utcnow(),
            color=style.Color.RED,
        )
        embed.set_footer(
            text=f"Banned by {mod.name}#{mod.discriminator}",
            icon_url=mod.avatar.url,
        )
        await ctx.send(embed=embed)


class Mod(commands.Cog):
    """
    Moderation related commands
    """

    COLOR = style.Color.SILVER
    ICON = ":tools:"

    def __init__(self, bot: commands.Bot):
        """
        Init with moderationmanager short mm
        """
        self.bot = bot
        self.db: asqlite.Connection = None
        self.mm: ModerationManager = None

    async def cog_load(self) -> None:
        """
        Load our sqlite db yay
        """
        self.db = await asqlite.connect("Databases/mod.db")
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS warns (
                case_id TEXT    PRIMARY KEY
                                NOT NULL,
                guild   TEXT    NOT NULL,
                mod     TEXT    NOT NULL,
                offender TEXT   NOT NULL,
                time    INT     NOT NULL,
                reason  TEXT,
                active  BOOL
            );
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS bans (
                case_id TEXT    PRIMARY KEY
                                NOT NULL,
                guild   TEXT    NOT NULL,
                mod     TEXT    NOT NULL,
                offender TEXT   NOT NULL,
                time    INT     NOT NULL,
                reason  TEXT,
                expires INT,
                active  BOOL
            );
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS mutes (
                case_id TEXT    PRIMARY KEY
                                NOT NULL,
                guild   TEXT    NOT NULL,
                mod     TEXT    NOT NULL,
                offender TEXT   NOT NULL,
                time    INT     NOT NULL,
                reason  TEXT,
                expires INT,
                active  BOOL
            );
            """
        )
        await self.bot.blogger.load("Mod")
        self.mm = ModerationManager(self.bot, self.db)

    async def cog_unload(self) -> None:
        """
        Unload our sqlite db when the cog is closed
        """
        await self.db.close()

    async def queue_infraction(self, _type: str, infraction: Infraction) -> None:
        """
        Queue infractions for moderation
        """
        await asyncio.sleep(int(time.time()) - infraction.expires)

    @tasks.loop(time=datetime.time(hour=5, minute=0, second=0))
    async def queue_tasks(self) -> None:
        """
        Queue infraction actions for the next hour
        """
        async with self.db.execute("""SELECT * FROM mutes;""") as cursor:
            for row in cursor:
                mute = Infraction(row)
                self.bot.loop.create_task(self.queue_infraction("mute", mute))

    @commands.hybrid_group(
        name="mod",
        description="""Description of command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def mod_group(self, ctx: commands.Context) -> None:
        """Command description"""

    @commands.hybrid_command(
        name="warn",
        description="""Warn a user""",
        help="""Warn a user""",
        brief="Warn a user",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 6.0, commands.BucketType.user)
    @commands.has_permissions(mute_members=True)
    async def warn_cmd(
        self,
        ctx: commands.Context,
        member: commands.Greedy[discord.Member],
        *,
        reason: str = "None",
    ) -> None:
        """
        Warn cmd
        """
        await self.mm.warn(ctx, ctx.author, member[0], reason)

    @commands.hybrid_command(
        name="mute",
        description="""Mute a user""",
        help="""Mute a user""",
        brief="Mute a user",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 6.0, commands.BucketType.user)
    @commands.has_permissions(mute_members=True)
    async def mute_cmd(
        self,
        ctx: commands.Context,
        member: commands.Greedy[discord.Member],
        *,
        reason: str = "None",
    ) -> None:
        """
        Warn cmd
        """
        await self.mm.warn(ctx, ctx.author, member[0], reason)

    @commands.hybrid_command(
        name="ban",
        description="""Ban a user from this guild""",
        help="""Ban a user from entering a guild because we don't like them""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 6.0, commands.BucketType.user)
    @commands.has_permissions(ban_members=True)
    async def ban_cmd(
        self, ctx: commands.Context, offender: discord.Member, *, reason: str = None
    ) -> None:
        """
        Ban a member, requires ban member permission
        """
        if offender == ctx.author:
            raise commands.BadArgument("You can't ban yourself idiot")

        if offender == self.bot.user:
            raise commands.BadArgument(
                "After all I've done for you, you try to ban me?"
            )

        try:
            await self.mm.ban(ctx, ctx.author, offender, reason)

        except Exception as e:
            error = discord.Embed(
                title="Error",
                description=f"""```diff
- {e}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=error)

    @commands.command(
        name="unban",
        description="""Unban a user using an id""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 6.0, commands.BucketType.user)
    @commands.has_permissions(ban_members=True)
    async def unban_cmd(
        self, ctx: commands.Context, member: int, reason: str = None
    ) -> None:
        """
        Unban a user using an id
        """

    @commands.group(
        name="modlogs",
        description="""Check someones latest modlogs""",
        help="""Check someones latest modlogs""",
        brief="Check someones latest modlogs",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 5.0, commands.BucketType.user)
    async def modlogs_group(self, ctx: commands.Context) -> None:
        """
        Check someones latest modlogs
        """
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @modlogs_group.command(
        name="channel",
        description="""Set the modlogs channel""",
        help="""Set the modlogs channel""",
        brief="Set the modlogs channel",
        aliases=["set"],
        enabled=True,
        hidden=False,
    )
    async def modlogs_channel(
        self, ctx: commands.Context, channel: discord.TextChannel
    ) -> None:
        """
        Set a channel for modlogs
        """
        data = await self.db_modlogs.find_one({"_id": ctx.guild.id})

        if not data:
            document = {
                "_id": ctx.guild.id,
                "channel": channel.id,
            }
            await self.db_modlogs.insert_one(document)

            modlogs_set = discord.Embed(
                title="Success",
                description=f"""Modlogs channel set to {channel.mention}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREEN,
            )
            modlogs_set.set_thumbnail(url=style.Emoji.IMAGE.check)
            await ctx.send(embed=modlogs_set)

        if data.get("channel") == channel.id:
            same_thing = discord.Embed(
                title="Error",
                description=f"""Modlogs channel is already set to {channel.mention}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.YELLOW,
            )
            await ctx.send(embed=same_thing)

        else:
            await self.db_modlogs.update_one(
                {"_id": ctx.guild.id}, {"$set": {"channel": channel.id}}
            )

            modlogs_changed = discord.Embed(
                title="Success",
                description=f"""Modlogs channel changed to {channel.mention}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREEN,
            )
            modlogs_changed.set_thumbnail(url=style.Emoji.IMAGE.check)
            await ctx.send(embed=modlogs_changed)

    @commands.Cog.listener()
    async def on_send_modlog(self, _type: str, modlog: str) -> None:
        """Send modlogs to the specified channel if not just return"""
        return


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog. Still need to fix this
    """
    await bot.add_cog(Mod(bot))
