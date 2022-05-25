import aioredis
import asyncio
import discord
from motor.motor_asyncio import AsyncIOMotorClient
from discord.ext import commands, tasks
from gears import style


"""
await self.bot.redis.set("Key", "Data") Set a key
value = await self.bot.redis.get("Key")
"""


class Databases(commands.Cog):
    """
    Database related things

    Currently using redis and mongodb
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.redis_updater.start()

    async def cog_load(self):
        """Connect to our Redis DB"""
        self.bot.redis = await aioredis.from_url(
            "redis://redis-18272.c273.us-east-1-2.ec2.cloud.redislabs.com:18272",
            username="",
            password=self.bot.config.get("Redis").get("Pass"),
            decode_responses=True,
        )
        await self.bot.printer.p_load("Redis")
        mongo_uri = (
            self.bot.config.get("Mongo")
            .get("URL")
            .replace("<Username>", self.bot.config.get("Mongo").get("User"))
            .replace("<Password>", self.bot.config.get("Mongo").get("Pass"))
        )
        self.bot.mongo = AsyncIOMotorClient(mongo_uri)
        await self.bot.printer.p_connect("MONGODB")

    async def cog_unload(self):
        """
        Stop task loop if cog unloaded
        """
        self.redis_updater.cancel()

    @commands.group()
    @commands.is_owner()
    async def redis(self, ctx: commands.Context) -> None:
        """Access stuff about redis"""
        if not ctx.invoked_subcommand:
            await ctx.send_help("redis")

    @redis.command()
    async def get(self, ctx: commands.Context, key):
        """Get a certain keys data"""
        data = await self.bot.redis.get(key)

        if not data:
            not_found = discord.Embed(
                title=f"Key {key} Not Found",
                description="""
                """,
            )
            return await ctx.send(embed=not_found)

        embed = discord.Embed(
            title="Redis Key Data",
            description=f"""```
{data}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.random(),
        )
        await ctx.send(embed=embed)

    @redis.command()
    async def add(self, ctx: commands.Context, key, value):
        """Add something to our db"""
        try:
            await self.bot.redis.set("key", "Data")
            embed = discord.Embed(
                title=f"""Added Key""",
                description=f"""```md
[{key}]({value})
```""",
            )
            return await ctx.send(embed=embed)

        except Exception as e:
            unable = discord.Embed(
                title="Error",
                description=f"""```diff
- {e}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=unable)

    @redis.command()
    async def search(self, ctx: commands.Context, *, pattern: str = "*"):
        """List all our keys"""
        keys = ""
        for count, value in enumerate(await self.bot.redis.keys(pattern), start=1):
            keys = f"""{keys}\n{count}. {value}"""

        if keys == "":
            keys = f"""[{pattern}][None]"""

        embed = discord.Embed(
            title=f"""Redis Keys in Database - {len(await self.bot.redis.keys("*"))}""",
            description=f"""```md
{keys}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.random(),
        )
        await ctx.send(embed=embed)

    @redis.command()
    async def info(self, ctx: commands.Context) -> None:
        """Show some info about our connection"""
        embed = discord.Embed(
            title="Redis Info",
            description=f"""```asciidoc
= ACL Info =
[ User: {await self.bot.redis.acl_whoami()} ]

= Connection Info =
[ User: {await self.bot.redis.client_getname()} ]
[ ID: {await self.bot.redis.client_id()}]

= Misc =
[ Database Size (Keys): {await self.bot.redis.dbsize()} ]
```""",
        )
        await ctx.send(embed=embed)

    @redis.command()
    async def cinfo(self, ctx: commands.Context) -> None:
        """Show complex info about our Redis DB"""
        data = await self.bot.redis.info()

        visual = ""

        for item in data.keys():
            visual = (
                f"""{visual}\n[ {item.replace("_", " ").capitalize()}: {data[item]} ]"""
            )

        embed = discord.Embed(
            title="Redis Complex Info",
            description=f"""```asciidoc
= Info =
{visual}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.random(),
        )
        await ctx.send(embed=embed)

    @redis.command()
    async def sa(self, ctx: commands.Context) -> None:
        """Show all data"""
        embed = discord.Embed(
            title="Attempting to fetch all data",
            description=f"""ETA {await self.bot.redis.dbsize() * 0.1} seconds""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.RED,
        )
        msg = await ctx.send(embed=embed)

        keys = await self.bot.redis.scan()

        visualiser = ""
        for key in keys[1]:
            visualiser = (
                f"""{visualiser}\n{key:15}: {await self.bot.redis.get(key):>5}"""
            )
            await asyncio.sleep(0.1)

        embed_done = discord.Embed(
            title="Finished",
            description=f"""```yaml
{visualiser}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        await msg.edit(embed=embed_done)

    @tasks.loop(hours=1.0)
    async def redis_updater(self):
        await self.bot.redis.set("updater", "0")
        await self.bot.redis.set("updater", "1")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Databases(bot))
