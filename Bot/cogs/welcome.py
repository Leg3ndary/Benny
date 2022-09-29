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

    COLOR = style.Color.GREEN
    ICON = "👋"

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
        data = json.dumps(embed.to_dict())
        return data

    async def to_embed(self, data: str) -> discord.Embed:
        """
        Convert a json serializable string into a discord embed
        """
        embed = discord.Embed.from_dict(json.loads(data))
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
    Anything to deal with members joining or leaving, this includes related roles
    """

    COLOR = style.Color.GREEN
    ICON = ":wave:"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init for the bot
        """
        self.bot = bot
        self.db: asqlite.Connection = None
        self.wm: WelcomeManager = None

    async def cog_load(self) -> None:
        """
        On cog load create a connection because yes
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
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS autoroles (
                guild TEXT  PRIMARY KEY
                                NOT NULL,
                role TEXT
            );
        """
        )

        self.wm = WelcomeManager(self.bot, self.db)

    async def cog_unload(self) -> None:
        """
        On cog unload, close connection
        """
        await self.db.close()

    async def autorole(self, member: discord.Member) -> None:
        """
        Give a user an autorole
        """
        guild = member.guild.id

        async with self.db.cursor() as cur:
            result = await (
                await cur.execute(
                    """SELECT role FROM autoroles WHERE guild = ?;""",
                    (str(guild)),
                )
            ).fetchone()

        if not result:
            return

        result = result["role"]

        role = discord.utils.get(member.guild.roles, id=int(result))
        await member.add_roles(role)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        On a member joining, welcome them! and give them roles if need be
        """
        self.bot.loop.create_task(self.wm.welcome(member))
        self.bot.loop.create_task(self.autorole(member))

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
        hidden=False,
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
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def welcome_set_group(self, ctx: commands.Context) -> None:
        """
        Set the welcome command
        """

    @commands.hybrid_group(
        name="autorole",
        description="""Description of command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    @commands.has_permissions(manage_guild=True)
    async def autorole_cmd(self, ctx: commands.Context) -> None:
        """
        Autorole command
        """
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @autorole_cmd.command(
        name="current",
        description="""Show the current autorole role""",
        help="""Show the current autorole role""",
        brief="Show the current autorole role",
        aliases=["show"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def autorole_current_cmd(self, ctx: commands.Context) -> None:
        """
        Show the current autorole role
        """
        async with self.db.cursor() as cur:
            result = await (
                await cur.execute(
                    """SELECT role FROM autoroles WHERE guild = ?;""",
                    (str(ctx.guild.id)),
                )
            ).fetchone()

            if result:
                result = result["role"]
                embed = discord.Embed(
                    title="Success",
                    description=f"""Currently your members will receive the role <@&{result}> ({result}) when they join""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.AQUA,
                )
                await ctx.reply(embed=embed)

            else:
                embed = discord.Embed(
                    title="Error",
                    description="""Sorry, but it doesn't seem like you have an autorole set up, you can set one up with the </autorole set:1019795609391222915> command.""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.RED,
                )
                await ctx.reply(embed=embed)

    @autorole_cmd.command(
        name="set",
        description="""Set a role for the autorole""",
        help="""Set a role for the autorole""",
        brief="Set a role for the autorole",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def autorole_set_cmd(self, ctx: commands.Context, role: discord.Role) -> None:
        """
        Set a role for the autorole
        """
        if ctx.me.roles[-1] <= role:
            raise commands.BadArgument(
                f"""I cannot assign a role higher than mine!
            
            The role {role.mention} is above my highest role ({ctx.me.roles[-1].mention})."""
            )

        if not ctx.bot_permissions.manage_roles:
            raise commands.BotMissingPermissions(["manage_roles"])

        async with self.db.cursor() as cur:
            result = await (
                await cur.execute(
                    """SELECT role FROM autoroles WHERE guild = ?;""",
                    (str(ctx.guild.id)),
                )
            ).fetchone()

            if result:
                result = result["role"]
                await cur.execute(
                    """UPDATE autoroles SET role = ? WHERE guild = ?;""",
                    (str(role.id), str(ctx.guild.id)),
                )
                embed = discord.Embed(
                    title="Success",
                    description=f"""Updated autorole to {role.mention} (Previously <@&{result}>)""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.GREEN,
                )
                await ctx.reply(embed=embed)

            else:
                await cur.execute(
                    """INSERT INTO autoroles (guild, role) VALUES (?, ?);""",
                    (str(ctx.guild.id), str(role.id)),
                )
                await self.db.commit()
                embed = discord.Embed(
                    title="Success",
                    description=f"""Added autorole {role.mention} successfully!""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.GREEN,
                )
                await ctx.reply(embed=embed)

    @autorole_cmd.command(
        name="delete",
        description="""Remove autorole from the server""",
        help="""Remove autorole from the server""",
        brief="Remove autorole from the server",
        aliases=["remove", "del"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def autorole_delete_cmd(self, ctx: commands.Context) -> None:
        """
        Remove autorole from the server
        """
        async with self.db.cursor() as cur:
            result = await (
                await cur.execute(
                    """SELECT role FROM autoroles WHERE guild = ?;""",
                    (str(ctx.guild.id)),
                )
            ).fetchone()

            if result:
                result = result["role"]
                await cur.execute(
                    """DELETE FROM autoroles WHERE guild = ?;""", (str(ctx.guild.id))
                )
                await self.db.commit()
                embed = discord.Embed(
                    title="Success",
                    description=f"""Removed autorole <@&{result}> ({result}) successfully!""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.GREEN,
                )
                await ctx.reply(embed=embed)

            else:
                embed = discord.Embed(
                    title="Error",
                    description="""Sorry, but it doesn't seem like you have an autorole set up, you can set one up with the </autorole set:1019795609391222915> command.""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.RED,
                )
                await ctx.reply(embed=embed)

    @commands.hybrid_group(
        name="stickyrole",
        description="""Set roles to be sticky, allowing users to rejoin with it""",
        help="""Set a role to be sticky, allowing users to rejoin with it""",
        brief="Set a role to be sticky, allowing users to rejoin with it",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def stickyrole_cmd(self, ctx: commands.Context) -> None:
        """
        Set a role to be sticky, allowing users to rejoin with it
        """
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @stickyrole_cmd.command(
        name="enable",
        description="""Enable sticky roles""",
        help="""Enable sticky roles""",
        brief="Enable sticky roles",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def stickyrole_enable_cmd(self, ctx: commands.Context) -> None:
        """
        Enable sticky roles
        """

    @stickyrole_cmd.command(
        name="disable",
        description="""Disable sticky roles""",
        help="""Disable sticky roles""",
        brief="Disable sticky roles",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def stickyrole_disable_cmd(self, ctx: commands.Context) -> None:
        """
        Disable stickyroles
        """


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Welcome(bot))
