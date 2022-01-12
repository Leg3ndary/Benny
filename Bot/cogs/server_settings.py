import aiosqlite
import asyncio
import discord
import discord.utils
from discord.ext import commands
from gears import style


"""
CREATE TABLE playlists(id integer NOT NULL, playlist_name text NOT NULL, songs text NOT NULL);

INSERT INTO tablename VALUES(values go here);
INSERT INTO playlists VALUES(id, playlist_name, songs);

SELECT * FROM playlists;

SELECT * FROM playlists WHERE id IS 1289739812739821;

ALTER TABLE playlists ADD COLUMN plays integer;

UPDATE playlists SET plays = 0 WHERE id=11111;

DELETE FROM playlists WHERE plays <= 1;
"""

"""
CREATE TABLE prefixes(server_id integer NOT NULL PRIMARY KEY, prefix1 text DEFAULT , )

"""

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

    def __init__(self, bot_prefixes) -> None:
        self.bot_prefixes = bot_prefixes

    def sanitize_prefix(self, prefix: str) -> str:
        """Sanitize a prefix and return it back clean"""
        return prefix.strip()[:25]
    
    async def generate_prefix_list(self, prefixes: tuple) -> list:
        """Generate a prefix list from a tuple"""
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
        Return a tuple of prefixes a guild has
        """
        async with aiosqlite.connect("server.db") as db:
            async with db.execute(
                """SELECT * FROM prefixes WHERE guild_id = ?;""", (str(guild_id),)
            ) as cursor:
                return await cursor.fetchone()

    async def add_prefix(self, guild_id: str, prefix: str) -> str:
        """
        Add a prefix to a guild
        """
        prefixes = await self.get_prefixes(guild_id)
        prefix = self.sanitize_prefix(prefix)

        if prefix in prefixes:
            return("ERROR:You already have this prefix as a prefix in your server")
        elif "" in prefixes:
            clear = 0
            for prefix_slot in prefixes:
                if prefix_slot == "":
                    pnum = "p" + str(clear)
                    async with aiosqlite.connect("server.db") as db:
                        # We don't worry about injection because it's literally not possible for pnum
                        await db.execute(f"""UPDATE prefixes SET {pnum} = ? WHERE guild_id = ?;""", (prefix, str(guild_id)))
                        await db.commit()
                        self.bot_prefixes[str(guild_id)] = await self.generate_prefix_list(await self.get_prefixes(guild_id))
                        return(f"SUCCESS:Added prefix `{prefix}` to your server!")
                else:
                    clear += 1
        else:
            return("ERROR:You've already hit the max of 25 prefixes!\nRemove some to add more")

    async def delete_prefix(self, guild_id: str, prefix: str) -> str:
        """
        Delete a prefix from a guild
        """
        prefixes = await self.get_prefixes(guild_id)
        prefix = self.sanitize_prefix(prefix)
        if prefix not in prefixes:
            return(f"ERROR:You don't have {prefix} as a prefix in your server")
        else:
            pnum = "p" + str(prefixes.index(prefix))
            async with aiosqlite.connect("server.db") as db:
                # We don't worry about injection because it's literally not possible for pnum
                await db.execute(f"""UPDATE prefixes SET {pnum} = "" WHERE guild_id = ?;""", (str(guild_id),))
                await db.commit()
                self.bot_prefixes[str(guild_id)] = await self.generate_prefix_list(await self.get_prefixes(guild_id))
                return(f"SUCCESS:Deleted prefix `{prefix}` from your server!")

    async def add_guild(self, guild_id: str) -> None:
        """Add a guild to our db with default prefixes"""
        async with aiosqlite.connect("server.db") as db:
            await db.execute("""INSERT INTO prefixes VALUES(?, "?", "", "", "", "", "", "", "", "", "", "", "", "", "", "");""", (str(guild_id),))
            await db.commit()
            # Since we already know that they should only one value, nice
            self.bot_prefixes[str(guild_id)] = ["?"]
            print(f"[SERVER SETTINGS] Added {guild_id} to the database")



class ServerSettings(commands.Cog):
    """Manage server settings like prefixes, welcome messages, etc"""

    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_load_prefixes(self):
        """
        Loading every prefix into a cache so we can quickly access it
        """
        self.bot.prefixes = {}
        async with aiosqlite.connect("server.db") as db:
            # Ha carl, this bot has 15 prefixes if you ever see this
            await db.execute(
                """CREATE TABLE IF NOT EXISTS prefixes(guild_id text, p1 text, p2 text, p3 text, p4 text, p5 text, p6 text, p7 text, p8 text, p9 text, p10 text, p11 text, p12 text, p13 text, p14 text, p15 text);"""
            )
            self.bot.prefix_manager = Prefixes(self.bot.prefixes)
        
        for guild in self.bot.guilds:
            prefix_tup = await self.bot.prefix_manager.get_prefixes(guild.id)
            if prefix_tup:
                self.bot.prefixes[str(guild.id)] = await self.bot.prefix_manager.generate_prefix_list(prefix_tup)
            else:
                # We didn't find the prefix added to to the db, add and add to prefixes
                await self.bot.prefix_manager.add_guild(guild.id)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Whenever we join a guild add our data"""
        await self.bot.prefix_manager.add_guild(guild.id)

    @commands.group(
        name="prefix",
        description="""Manage or view prefixes""",
        help="""NMot done""",
        brief="""also not done :eyes:""",
        usage="Usage",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.guild_only()
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    @commands.has_permissions(manage_messages=True)
    async def prefix_manage(self, ctx):
        """Command description"""
        if not ctx.invoked_subcommand:
            prefixes = await self.bot.prefix_manager.generate_prefix_list(await self.bot.prefix_manager.get_prefixes(ctx.guild.id))
            prefix_visual = ""
            for count, prefix in enumerate(prefixes, start=1):
                prefix_visual += f"\n{count}. {prefix}"
            embed = discord.Embed(
                title=f"Prefixes",
                description=f"""Viewing prefixes for {ctx.guild.name}
                {prefix_visual}""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color()
            )
            await ctx.send(embed=embed)

    @prefix_manage.command(
        name="add",
        description="""Add a prefix""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        usage="Usage",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def add_prefix(self, ctx, *, prefix: str):
        """Command description"""
        add_prefix = await self.bot.prefix_manager.add_prefix(ctx.guild.id, prefix)
        
        if add_prefix.split(":")[0] == "SUCCESS":
            embed = discord.Embed(
                title=f"Success",
                description=f"""{add_prefix.split(":")[1]}""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("green")
            )
            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(
                title=f"Error",
                description=f"""{add_prefix.split(":")[1]}""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red")
            )
            await ctx.send(embed=embed)

    @prefix_manage.command(
        name="remove",
        description="""Remove a prefix""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        usage="Usage",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def remove_prefix(self, ctx, *, prefix: str):
        """Command description"""
        del_prefix = await self.bot.prefix_manager.delete_prefix(ctx.guild.id, prefix)
        
        if del_prefix.split(":")[0] == "SUCCESS":
            embed = discord.Embed(
                title=f"Success",
                description=f"""{del_prefix.split(":")[1]}""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("green")
            )
            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(
                title=f"Error",
                description=f"""{del_prefix.split(":")[1]}""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red")
            )
            await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(ServerSettings(bot))
