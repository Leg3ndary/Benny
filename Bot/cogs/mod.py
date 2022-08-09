import datetime
import re
import time

import asqlite
import discord
import discord.utils
import parsedatetime
from discord.ext import commands
from gears import style


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

    async def pull_time(self, string: str) -> float:
        """
        Pull the time from a string
        """
        # time_struct, parse_status = self.calendar.parse(string) original, pylint said to remove it
        time_struct = self.calendar.parse(string)
        return datetime.datetime(*time_struct[:6]).timestamp()

    async def warn(
        self, ctx: commands.Context, member: discord.Member, reason: str
    ) -> None:
        """
        Warn a member
        """
        future_time = await self.pull_time(reason)
        current_time = int(time.time())

        user = self.bot.get_user(ctx.author.id) or (
            await self.bot.fetch_user(ctx.author.id)
        )

        if future_time <= current_time:
            await self.db.execute(
                """INSERT INTO warns VALUES(?, ?, ?, ?, ?, ?);""",
                (
                    await self.get_count(str(ctx.guild.id)),
                    member.id,
                    ctx.author.id,
                    reason,
                    current_time,
                    future_time,
                ),
            )
            description = f"{reason}\n\nExpires in <t:{future_time}:R>"

        else:
            await self.db.execute(
                """INSERT INTO warns VALUES(?, ?, ?, ?, ?);""",
                (
                    await self.get_count(str(ctx.guild.id)),
                    member.id,
                    ctx.author.id,
                    reason,
                    current_time,
                    None,
                ),
            )
            description = reason
        await self.db.commit()

        embed = discord.Embed(
            title=f"Warned {user.name}#{user.discriminator}",
            description=description,
            timestamp=discord.utils.utcnow(),
            color=style.Color.YELLOW,
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
                case_id INT    PRIMARY KEY
                                NOT NULL,
                guild   TEXT    NOT NULL,
                mod     TEXT    NOT NULL,
                time    INT     NOT NULL,
                reason  TEXT,
                active  BOOL
            );
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS bans (
                case_id INT    PRIMARY KEY
                                NOT NULL,
                guild   TEXT    NOT NULL,
                mod     TEXT    NOT NULL,
                time    INT     NOT NULL,
                reason  TEXT,
                expires INT
            );
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS mutes (
                case_id INT    PRIMARY KEY
                                NOT NULL,
                guild   TEXT    NOT NULL,
                mod     TEXT    NOT NULL,
                time    INT     NOT NULL,
                reason  TEXT,
                expires INT
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
        await self.mm.warn(ctx, member[0], reason)

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
        self, ctx: commands.Context, user: discord.Member = None, *, reason: str = None
    ) -> None:
        """
        Ban a member, requires ban member permission
        """
        if user == ctx.author:
            same_user_embed = discord.Embed(
                title="Error",
                description="""You cannot ban yourself!""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=same_user_embed)

        elif not user and re.match(r"[0-9]{15,19}", str(user)):
            try:
                user = await self.bot.get_user(int(user))
            except:
                user = await self.bot.fetch_user(int(user))

        elif not user:
            none_mentioned = discord.Embed(
                title="Error",
                description="""The user {user} was not found.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=none_mentioned)

        elif user.id == self.bot.user.id:
            ban_bot = discord.Embed(
                title="Rude",
                description="""After all I've done for you, you try to ban me?""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.YELLOW,
            )
            await ctx.send(embed=ban_bot)

        else:
            try:
                user_reason = f"Banned by {ctx.author}: "
                if not reason:
                    reason = user_reason + "No Reason Specified"
                else:
                    reason = user_reason + reason
                await user.ban(reason=reason)
                await self.db.execute(
                    """INSERT INTO bans VALUES(?, ?, ?, ?);""",
                    (user.id, ctx.author.id, reason, int(time.time())),
                )
                await self.db.commit()
                banned_embed = discord.Embed(
                    title=f"Banned {user}",
                    description=f"""```diff
- {reason} -
```""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.GREEN,
                )
                await ctx.send(embed=banned_embed)

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
        if not re.match(r"[0-9]{15,19}", str(member)):
            embed = discord.Embed(
                title="Error",
                description=f"""Sorry but `{member}` doesn't seem to be a valid id.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)
        else:
            try:
                member = await ctx.guild.fetch_ban(discord.Object(id=member))
            except discord.NotFound:
                embed = discord.Embed(
                    title="Not Banned",
                    description="""This user doesn't seem to be banned...""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.YELLOW,
                )
                await ctx.send(embed=embed)
                return

            reason = "Unbanned by: "

            await ctx.guild.unban(discord.Object(id=member), reason)

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
