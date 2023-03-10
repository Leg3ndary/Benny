import asqlite
import discord
import discord.utils
from colorama import Fore
from discord.ext import commands
from gears import style
from interfaces.database import BennyDatabases


class UserAccess:
    """
    Class to access our users info
    """

    def __init__(self, db: asqlite.Connection) -> None:
        """
        Init with the userdb
        """
        self.db = db

    async def create_user(self, user_id: str) -> tuple:
        """
        Create a user in our small database
        """
        await self.db.execute(
            """INSERT INTO settings_users VALUES(?, 0, False);""", (user_id,)
        )
        await self.db.commit()

    async def get_user(self, user_id: str) -> tuple:
        """
        Get a users info
        """
        async with self.db.execute(
            """SELECT * FROM settings_users WHERE user_id = ?;""", (user_id,)
        ) as cursor:
            if not cursor.fetchone():
                await self.create_user(user_id)
                return await self.get_user(user_id)
            else:
                return cursor.fetchone()


class PrefixManager:
    """
    A way to update prefixes both in the bot's cache and in the database with nice simple functions
    """

    def __init__(self, bot: commands.Bot, db: asqlite.Connection) -> None:
        """
        Init
        """
        self.bot = bot
        self.db = db

    def sanitize_prefix(self, prefix: str) -> str:
        """
        Sanitize a prefix and return it back clean

        Parameters
        ----------
        prefix: str
            The prefix to sanitize

        Returns
        -------
        str
        """
        if ":|:" in prefix:
            raise commands.BadArgument("Why do you have `:|:` as a prefix...")
        return prefix.strip()[:25]

    def prefixes_to_string(self, prefixes: list) -> str:
        """
        Turn prefix list into string

        Parameters
        ----------
        prefixes: list
            A list of prefixes

        Returns
        -------
        str
        """
        return ":|:".join(prefixes)

    async def get_prefixes(self, guild: str) -> list:
        """
        Return a tuple of prefixes a guild has

        Parameters
        ----------
        guild: str
            The guild id

        Returns
        -------
        list
        """
        async with self.db.execute(
            """SELECT prefixes FROM settings_prefixes WHERE guild = ?;""", (str(guild),)
        ) as cursor:
            result = await cursor.fetchone()

        if result:
            return sorted((result)[0].split(":|:"), key=len)
        else:
            await self.add_guild(guild)
            return [self.bot.PREFIX]

    async def add_prefix(self, guild: str, prefix: str) -> None:
        """
        Add a prefix to a guild, adds to both our database and cache

        Parameters
        ----------
        guild: str
            The guild id
        prefix: str
            The prefix which we will sanitize

        Returns
        -------
        None
        """
        prefixes = await self.get_prefixes(guild)
        prefix = self.sanitize_prefix(prefix)

        if prefix in prefixes:
            raise commands.BadArgument(
                f"You already have {prefix} as a prefix in your server"
            )

        elif len(prefixes) >= 15:
            raise commands.BadArgument("You can only have up to 15 prefixes")

        elif prefix == "":
            raise commands.BadArgument("You cannot have an empty prefix")

        else:
            prefixes.append(prefix)
            if prefixes:
                prefixes = sorted(prefixes, key=len)
            self.bot.prefixes[str(guild)] = prefixes
            await self.db.execute(
                """UPDATE settings_prefixes SET prefixes = ? WHERE guild = ?;""",
                (self.prefixes_to_string(prefixes), str(guild)),
            )
            await self.db.commit()
        return

    async def delete_prefix(self, guild: str, prefix: str) -> None:
        """
        Delete a prefix from a guild, deletes to both our database and cache

        Parameters
        ----------
        guild: str
            The guild id
        prefix: str
            The prefix which we will also sanitize

        Returns
        -------
        None
        """
        prefixes = await self.get_prefixes(guild)
        prefix = self.sanitize_prefix(prefix)

        if prefix not in prefixes:
            raise commands.BadArgument(
                f"You don't have {prefix} as a prefix in your server"
            )
        else:
            prefixes.remove(prefix)
            self.bot.prefixes[str(guild)] = prefixes
            await self.db.execute(
                """UPDATE settings_prefixes SET prefixes = ? WHERE guild = ?;""",
                (self.prefixes_to_string(prefixes), str(guild)),
            )
            await self.db.commit()

    async def add_guild(self, guild: str) -> None:
        """
        Add a guild to our db with default prefixes

        Parameters
        ----------
        guild: str
            The guild id to add.

        Returns
        -------
        None
        """
        self.bot.prefixes[str(guild)] = [self.bot.PREFIX]
        await self.db.execute(
            """INSERT INTO settings_prefixes VALUES(?, ?);""",
            (str(guild), self.bot.PREFIX),
        )
        await self.db.commit()
        await self.bot.terminal.cog(
            self.bot.terminal.gen_category(f"{Fore.CYAN}SERVER SETTINGS"),
            f"Added {guild} to prefixes",
        )
        return

    async def delete_guild(self, guild: str) -> None:
        """
        Delete a guild from our db, remove all prefixes

        Parameters
        ----------
        guild: str
            The guild to delete the data from

        Returns
        -------
        None
        """
        del self.bot.prefixes[str(guild)]
        await self.db.execute(
            """DELETE FROM settings_prefixes WHERE guild = ?;""", (str(guild),)
        )
        await self.db.commit()
        await self.bot.terminal.cog(
            self.bot.terminal.gen_category(f"{Fore.CYAN}SERVER SETTINGS"),
            f"Deleted {guild} from prefixes",
        )
        return


class Settings(commands.Cog):
    """
    Manage server settings like prefixes, welcome messages, etc
    """

    COLOR = style.Color.AQUA
    ICON = "⚙️"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init for the bot
        """
        self.bot = bot
        self.databases: BennyDatabases = bot.databases

    async def cog_load(self) -> None:
        """
        On cog load, load up some users
        """
        await self.databases.users.execute(
            """
            CREATE TABLE IF NOT EXISTS settings_users (
                id           TEXT    PRIMARY KEY
                                    NOT NULL,
                patron_level INTEGER NOT NULL
                                    DEFAULT (0),
                blacklisted  BOOLEAN DEFAULT (False)
                                    NOT NULL,
                timezone     TEXT    DEFAULT (NULL)
            );
            """
        )
        await self.databases.users.commit()
        await self.bot.terminal.load("Users")

    async def cog_unload(self) -> None:
        """
        On cog unload, close connections
        """
        # await self.databases.users.close()
        # await self.databases.servers.close()
        # we don't need to close any connections anymore

    @commands.Cog.listener()
    async def on_load_prefixes(self) -> None:
        """
        Loading every prefix into a cache so we can quickly access it
        """
        self.bot.prefixes = {}
        self.bot.prefix_manager = PrefixManager(self.bot, self.databases.servers)

        await self.databases.servers.execute(
            """
            CREATE TABLE IF NOT EXISTS settings_prefixes (
                guild       TEXT PRIMARY KEY,
                prefixes    TEXT
            );
            """
        )
        for guild in self.bot.guilds:
            prefixes = await self.bot.prefix_manager.get_prefixes(guild.id)
            self.bot.prefixes[str(guild.id)] = prefixes

        self.bot.LOADED_PREFIXES = True

        await self.bot.terminal.load("Prefixes")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """
        Whenever we join a guild add our data
        """
        await self.bot.prefix_manager.add_guild(guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """
        Whenever we leave a guild, remove prefix data
        """
        await self.bot.prefix_manager.delete_guild(guild.id)

    @commands.group(
        name="prefix",
        description="""View all of your servers prefixes in a neat way""",
        help="""View all of your prefixes""",
        brief="""also not done :eyes:""",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.guild_only()
    @commands.cooldown(2.0, 5.0, commands.BucketType.user)
    async def prefix(self, ctx: commands.Context) -> None:
        """
        Prefix group for commands
        """
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @prefix.command(
        name="list",
        description="""Description of command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=["view", "config"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def prefix_list_cmd(self, ctx: commands.Context) -> None:
        """
        List prefixes for a server
        """
        prefixes = await self.bot.prefix_manager.get_prefixes(ctx.guild.id)

        prefix_visual = ""
        for count, prefix in enumerate(prefixes, start=1):
            prefix_visual += f"\n{count}. {prefix}"
        embed = discord.Embed(
            title="Prefixes",
            description=f"""Viewing prefixes for {ctx.guild.name}
```md
{prefix_visual}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        await ctx.send(embed=embed)

    @prefix.command(
        name="add",
        description="""Add a prefix to said guild""",
        help="""Add a prefix to your server
        Prefix may not have spaces before or after it, spaces inbetween are fine
        You may have up to 15 different prefixes""",
        brief="""Add a prefix to your server""",
        aliases=["create", "+"],
        enabled=True,
        hidden=False,
    )
    @commands.has_permissions(manage_messages=True)
    async def add_prefix(self, ctx: commands.Context, *, prefix: str):
        """
        Add a prefix to a server
        """
        await self.bot.prefix_manager.add_prefix(ctx.guild.id, prefix)

        embed = discord.Embed(
            title="Success",
            description=f"""Successfully added `{prefix}` to your server""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        await ctx.send(embed=embed)

    @prefix.command(
        name="remove",
        description="""Remove a prefix from said guild""",
        help="""Remove a prefix from your server
        You must always have at least one prefix in your server.""",
        brief="""Remove a prefix from your server""",
        aliases=["del", "rm", "delete", "-"],
        enabled=True,
        hidden=False,
    )
    @commands.has_permissions(manage_messages=True)
    async def remove_prefix(self, ctx: commands.Context, *, prefix: str):
        """
        Remove a prefix from your server
        """
        await self.bot.prefix_manager.delete_prefix(ctx.guild.id, prefix)

        embed = discord.Embed(
            title="Prefix Removed",
            description=f"""Successfully removed `{prefix}` from your server""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        await ctx.send(embed=embed)

    @commands.group(
        name="premium",
        description="""View premium perks and what you have""",
        help="""View premium related info and perks""",
        brief="""View premium related info""",
        aliases=["prem"],
        enabled=True,
        hidden=False,
    )
    @commands.guild_only()
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def premium_info(self, ctx: commands.Context) -> None:
        """
        Premium group for commands
        """
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @premium_info.command(
        name="add",
        description="""Add premium to said guild""",
        help="""Add premium to a server if it doesn't already have it""",
        brief="""Add a prefix to your server""",
        aliases=["create", "+"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def add_premium(self, ctx: commands.Context, *, prefix: str):
        """
        Add premium to the bot
        """
        return

    @premium_info.command(
        name="remove",
        description="""Remove a prefix from said guild""",
        help="""Remove a prefix from your server
        You must always have at least one prefix in your server.""",
        brief="""Remove a prefix from your server""",
        aliases=["del", "rm", "delete", "-"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def remove_premium(self, ctx: commands.Context, *, prefix: str):
        """
        Remove premium from a server
        """
        return


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Settings(bot))
