import asyncio
import json

import asqlite
import discord
import discord.utils
from discord.ext import commands
from gears import style


class WelcomeManager:
    """
    Managing welcoming and related things
    """

    def __init__(self, bot: commands.Bot, db: asqlite.Connection) -> None:
        """
        Init method
        """
        self.bot = bot
        self.db = db

    async def to_str(self, text: str, embed: discord.Embed) -> str:
        """
        Convert a discord embed object into a string to save to our db
        """
        data = await self.bot.loop.run_in_executor(None, json.dumps(), embed.to_dict())
        return data

    async def to_embed(self, data: str) -> discord.Embed:
        """
        Convert a json serializable string into a discord embed
        """
        embed = discord.Embed.from_dict(
            await self.bot.loop.run_in_executor(None, json.loads(), data)
        )
        return embed

    async def welcome(self, member: discord.Member) -> None:
        """
        Welcome a user!
        """
        guild = member.guild.id

        async with self.db.cursor() as cur:
            result = await (
                await cur.execute(
                    """SELECT welcome_channel FROM welcome WHERE guild = ?;""",
                    (str(guild)),
                )
            ).fetchone()

        if not result:
            return

        channel = self.bot.get_channel(result) or (await self.bot.fetch_channel(result))

        embed = await self.to_embed(result)
        await channel.send(embed=embed)

    async def goodbye(self, member: discord.Member) -> None:
        """
        Say goodbye to a user!
        """
        guild = member.guild.id

        async with self.db.cursor() as cur:
            result = await (
                await cur.execute(
                    """SELECT goodbye_channel FROM welcome WHERE guild = ?;""",
                    (str(guild)),
                )
            ).fetchone()

        if not result:
            return
        
        channel = self.bot.get_channel(result) or (await self.bot.fetch_channel(result))

        embed = await self.to_embed(result)
        await channel.send(embed=embed)


class Welcome(commands.Cog):
    """
    Anything to deal with welcoming or leaving
    """

    COLOR = style.Color.GREEN
    ICON = ":wave:"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init for the bot
        """
        self.bot = bot

    async def cog_load(self) -> None:
        """
        On cog load create a connection because
        """
        self.db: asqlite.Connection = await asqlite.connect("Databases/server.db")

        await self.db.execute(
            """
        CREATE TABLE IF NOT EXISTS welcome (
            guild           TEXT    PRIMARY KEY
                                        NOT NULL,
            welcome         TEXT,
            welcome_channel TEXT,
            goodbye         TEXT,
            goodbye_channel TEXT
        );
        """
        )

        self.wm = WelcomeManager(self.bot, self.db)

    async def cog_unload(self) -> None:
        """
        On cog unload, close connection
        """
        await self.db.close()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        On a member joining, welcome them!
        """
        await self.wm.welcome(member)

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent) -> None:
        """
        On member remove check if we have the user cached and move on accordingly
        """
        guild = self.bot.get_guild(payload.guild_id) or (
            await self.bot.fetch_guild(payload.guild_id)
        )

        member = guild.get_member(payload.user.id) or (
            await guild.fetch_member(payload.user.id)
        )

        await self.wm.goodbye(member)

    @commands.hybrid_group(
        name="welcome",
        description="""Welcome Group""",
        help="""Welcome Group""",
        brief="Welcome Group",
        aliases=[],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(2.0, 5.0, commands.BucketType.user)
    async def welcome_group(self, ctx: commands.Context) -> None:
        """
        Welcome group
        """
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @welcome_group.command(
        name="set",
        description="""Set the welcome command""",
        help="""Set the welcome command""",
        brief="Set the welcome command",
        aliases=[],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def welcome_set_group(self, ctx: commands.Context) -> None:
        """
        Set the welcome command
        """



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Welcome(bot))
