import asqlite
from colorama import Fore
import discord
import discord.utils
from discord.ext import commands
from gears import style


"""
Prefix Table Schema
CREATE TABLE IF NOT EXISTS prefixes(guild_id text, p1 text, p2 text, p3 text, p4 text, p5 text, p6 text, p7 text, p8 text, p9 text, p10 text, p11 text, p12 text, p13 text, p14 text, p15 text);

INSERT INTO prefixes VALUES(guild_id, "?", "", "", "", "", "", "", "", "", "", "", "", "", "", "");

UPDATE prefixes SET pnumhere WHERE guild_id = 'guildidhere';
"""


class Prefixes:
    """
    A way to update prefixes both in the bot's cache and in the database with nice simple functions
    """

    def __init__(self, bot) -> None:
        self.bot = bot

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
        return prefix.strip()[:25]

    async def generate_prefix_list(self, prefixes: tuple) -> list:
        """
        Generate a prefix list from a tuple, skipping duplicates and emptys.

        Parameters
        ----------
        prefixes: tuple
            A tuple of prefixes, ignore the first as that will be the guild id

        Returns
        -------
        list
        """
        prefix_list = []

        count = True
        for prefix in prefixes:
            if count:
                count = False
            elif prefix == "":
                pass
            elif prefix in prefix_list:
                # Shouldn't ever happen, but just in case
                pass
            else:
                prefix_list.append(prefix)
        return prefix_list

    async def get_prefixes(self, guild_id: str) -> tuple:
        """
        Return a tuple of prefixes a guild has, first item is the guild_id

        Parameters
        ----------
        guild_id: str
            The guild id

        Returns
        -------
        tuple
        """
        async with asqlite.connect("Databases/server.db") as db:
            async with db.execute(
                """SELECT * FROM prefixes WHERE guild_id = ?;""", (str(guild_id),)
            ) as cursor:
                return await cursor.fetchone()

    async def add_prefix(self, guild_id: str, prefix: str) -> str:
        """
        Add a prefix to a guild, adds to both our database and cache

        Parameters
        ----------
        guild_id: str
            The guild id
        prefix: str
            The prefix which we will sanitize

        Returns
        -------
        str
        """
        prefixes = await self.get_prefixes(guild_id)
        prefix = self.sanitize_prefix(prefix)

        if prefix in prefixes:
            return "ERROR:You already have this prefix as a prefix in your server"
        elif "" in prefixes:
            clear = 0
            for prefix_slot in prefixes:
                if prefix_slot == "":
                    pnum = "p" + str(clear)
                    async with asqlite.connect("Databases/server.db") as db:
                        # We don't worry about injection because it's literally not possible for pnum
                        await db.execute(
                            f"""UPDATE prefixes SET {pnum} = ? WHERE guild_id = ?;""",
                            (prefix, str(guild_id)),
                        )
                        await db.commit()
                        self.bot.prefixes[
                            str(guild_id)
                        ] = await self.generate_prefix_list(
                            await self.get_prefixes(guild_id)
                        )
                        return f"SUCCESS:Added prefix `{prefix}` to your server!"
                else:
                    clear += 1
        else:
            return "ERROR:You've already hit the max of 15 prefixes!\nRemove some to add more"

    async def delete_prefix(self, guild_id: str, prefix: str) -> str:
        """
        Delete a prefix from a guild, deletes to both our database and cache

        Parameters
        ----------
        guild_id: str
            The guild id
        prefix: str
            The prefix which we will also sanitize

        Returns
        -------
        str
        """
        prefixes = tuple(await self.get_prefixes(guild_id))
        prefix = self.sanitize_prefix(prefix)
        if prefix not in prefixes:
            return f"ERROR:You don't have {prefix} as a prefix in your server"
        elif len(prefixes) == 2:
            return f"ERROR:You must have at least one prefix for the bot at all times!"
        else:
            pnum = "p" + str(prefixes.index(prefix))
            async with asqlite.connect("Databases/server.db") as db:
                # We don't worry about injection because it's literally not possible for pnum
                await db.execute(
                    f"""UPDATE prefixes SET {pnum} = "" WHERE guild_id = ?;""",
                    (str(guild_id),),
                )
                await db.commit()
                self.bot.prefixes[str(guild_id)] = await self.generate_prefix_list(
                    await self.get_prefixes(guild_id)
                )
                return f"SUCCESS:Deleted prefix `{prefix}` from your server!"

    async def add_guild(self, guild_id: str) -> None:
        """
        Add a guild to our db with default prefixes

        Parameters
        ----------
        guild_id: str
            The guild id to add.

        Returns
        -------
        None
        """
        async with asqlite.connect("Databases/server.db") as db:
            await db.execute(
                """INSERT INTO prefixes VALUES(?, "?", "", "", "", "", "", "", "", "", "", "", "", "", "", "");""",
                (str(guild_id),),
            )
            await db.commit()
            # Since we already know that they should only one value, nice
            self.bot.prefixes[str(guild_id)] = ["?"]
            await self.bot.printer.print_cog(
                await self.bot.printer.generate_category(f"{Fore.CYAN}SERVER SETTINGS"),
                f"Added {guild_id} to prefixes",
            )

    async def delete_guild(self, guild_id: str) -> None:
        """
        Delete a guild to our db, remove all prefixes

        Parameters
        ----------
        guild_id: str
            The guild_id to delete the data from

        Returns
        -------
        None
        """
        async with asqlite.connect("Databases/server.db") as db:
            await db.execute(
                """DELETE FROM prefixes WHERE guild_id = ?;""", (str(guild_id),)
            )
            await db.commit()
            del self.bot.prefixes[str(guild_id)]
            await self.bot.printer.print_cog(
                await self.bot.printer.generate_category(f"{Fore.CYAN}SERVER SETTINGS"),
                f"Deleted {guild_id} from  prefixes",
            )


class Settings(commands.Cog):
    """Manage server settings like prefixes, welcome messages, etc"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_load_prefixes(self):
        """
        Loading every prefix into a cache so we can quickly access it
        """
        self.bot.prefixes = {}
        async with asqlite.connect("Databases/server.db") as db:
            # Ha carl, this bot has 15 prefixes if you ever see this
            await db.execute(
                """CREATE TABLE IF NOT EXISTS prefixes (
                    guild_id TEXT PRIMARY KEY,
                    p1       TEXT,
                    p2       TEXT,
                    p3       TEXT,
                    p4       TEXT,
                    p5       TEXT,
                    p6       TEXT,
                    p7       TEXT,
                    p8       TEXT,
                    p9       TEXT,
                    p10      TEXT,
                    p11      TEXT,
                    p12      TEXT,
                    p13      TEXT,
                    p14      TEXT,
                    p15      TEXT
                );
                """
            )
            self.bot.prefix_manager = Prefixes(self.bot)

        for guild in self.bot.guilds:
            prefix_tup = await self.bot.prefix_manager.get_prefixes(guild.id)
            if prefix_tup:
                self.bot.prefixes[
                    str(guild.id)
                ] = await self.bot.prefix_manager.generate_prefix_list(prefix_tup)
            else:
                # We didn't find the prefix added to to the db, add and add to prefixes
                await self.bot.prefix_manager.add_guild(guild.id)

        await self.bot.printer.print_load("Prefixes")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """
        Whenever we join a guild add our data
        """
        await self.bot.prefix_manager.add_guild(guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
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
    @commands.cooldown(1.0, 3.0, commands.BucketType.user)
    @commands.has_permissions(manage_messages=True)
    async def prefix_manage(self, ctx):
        """
        Prefix group for commands
        """
        if not ctx.invoked_subcommand:
            prefixes = await self.bot.prefix_manager.generate_prefix_list(
                await self.bot.prefix_manager.get_prefixes(ctx.guild.id)
            )
            prefix_visual = ""
            for count, prefix in enumerate(prefixes, start=1):
                prefix_visual += f"\n{count}. {prefix}"
            embed = discord.Embed(
                title=f"Prefixes",
                description=f"""Viewing prefixes for {ctx.guild.name}
```md
{prefix_visual}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color(),
            )
            await ctx.send(embed=embed)

    @prefix_manage.command(
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
    async def add_prefix(self, ctx, *, prefix: str):
        """Command description"""
        add_prefix = await self.bot.prefix_manager.add_prefix(ctx.guild.id, prefix)

        if add_prefix.split(":")[0] == "SUCCESS":
            embed = discord.Embed(
                title=f"Success",
                description=f"""{add_prefix.split(":")[1]}""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("green"),
            )
            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(
                title=f"Error",
                description=f"""{add_prefix.split(":")[1]}""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            await ctx.send(embed=embed)

    @prefix_manage.command(
        name="remove",
        description="""Remove a prefix from said guild""",
        help="""Remove a prefix from your server
        You must always have at least one prefix in your server.""",
        brief="""Remove a prefix from your server""",
        aliases=["del", "rm", "delete", "-"],
        enabled=True,
        hidden=False,
    )
    async def remove_prefix(self, ctx, *, prefix: str):
        """Remove a prefix from your server"""
        del_prefix = await self.bot.prefix_manager.delete_prefix(ctx.guild.id, prefix)

        if del_prefix.split(":")[0] == "SUCCESS":
            embed = discord.Embed(
                title=f"Success",
                description=f"""{del_prefix.split(":")[1]}""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("green"),
            )
            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(
                title=f"Error",
                description=f"""{del_prefix.split(":")[1]}""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
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
    async def premium_info(self, ctx):
        """
        Premium group for commands
        """
        if not ctx.invoked_subcommand:
            pass

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
    async def add_premium(self, ctx, *, prefix: str):
        """Add premium to the bot"""
        pass

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
    async def remove_premium(self, ctx, *, prefix: str):
        """Command description"""
        pass


def setup(bot):
    bot.add_cog(Settings(bot))
