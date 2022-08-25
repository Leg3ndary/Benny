import asyncio

import discord
from discord.ext import commands, tasks
from gears import style
from motor.motor_asyncio import AsyncIOMotorClient
from redis import asyncio as aioredis

"""
await self.bot.redis.set("Key", "Data") Set a key
value = await self.bot.redis.get("Key")
"""


class Databases(commands.Cog):
    """
    Database related things

    Currently using redis and mongodb
    """

    COLOR = style.Color.GREEN
    ICON = ":floppy_disk:"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Constructor for databases...
        """
        self.bot = bot
        self.redis_updater.start()

    async def cog_load(self) -> None:
        """
        Connect to our Redis DB
        """
        self.bot.redis = await aioredis.from_url(
            self.bot.config.get("Redis").get("URL"),
            username="",
            password=self.bot.config.get("Redis").get("Pass"),
            decode_responses=True,
        )
        await self.bot.blogger.load("Redis")
        mongo_uri = (
            self.bot.config.get("Mongo")
            .get("URL")
            .replace("<Username>", self.bot.config.get("Mongo").get("User"))
            .replace("<Password>", self.bot.config.get("Mongo").get("Pass"))
        )
        self.bot.mongo = AsyncIOMotorClient(mongo_uri)
        await self.bot.blogger.connect("MONGODB")

    async def cog_unload(self) -> None:
        """
        Stop task loop if cog unloaded
        """
        self.redis_updater.cancel()

    @commands.group(
        name="redis",
        description="""Redis Group""",
        help="""Redis Group""",
        brief="Redis Group",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    @commands.is_owner()
    async def redis_group(self, ctx: commands.Context) -> None:
        """
        Access stuff about redis
        """
        if not ctx.invoked_subcommand:
            await ctx.send_help("redis")

    @redis_group.command(
        name="get",
        description="""Get a keys value""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=["show"],
        enabled=True,
        hidden=False,
    )
    async def redis_get_cmd(self, ctx: commands.Context, key: str) -> None:
        """
        Get a certain keys value
        """
        data = await self.bot.redis.get(key)

        if not data:
            not_found = discord.Embed(
                title=f"Key {key} Not Found",
                description="""
                """,
            )
            await ctx.send(embed=not_found)

        else:
            embed = discord.Embed(
                title="Redis Key Data",
                description=f"""```
{data}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.random(),
            )
            await ctx.send(embed=embed)

    @redis_group.command(
        name="add",
        description="""Add a value to redis""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=["set", "+"],
        enabled=True,
        hidden=False,
    )
    async def redis_add_cmd(
        self, ctx: commands.Context, key: str, *, value: str
    ) -> None:
        """
        Add something to our db
        """
        try:
            await self.bot.redis.set(key, value)
            embed = discord.Embed(
                title="""Added Key""",
                description=f"""```md
[{key}]({value})
```""",
            )
            await ctx.send(embed=embed)

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

    @redis_group.command(
        name="search",
        description="""Search for a key""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    async def redis_search_cmd(
        self, ctx: commands.Context, *, pattern: str = "*"
    ) -> None:
        """
        List all our keys
        """
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

    @redis_group.command(
        name="info",
        description="""Info about redis""",
        help="""Info about redis""",
        brief="Info about redis",
        aliases=["i"],
        enabled=True,
        hidden=False,
    )
    async def redis_info_cmd(self, ctx: commands.Context) -> None:
        """
        Show some info about our connection
        """
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

    @redis_group.command(
        name="cinfo",
        description="""Complex info about redis""",
        help="""Complex info about redis""",
        brief="Complex info about redis",
        aliases=["complex", "c"],
        enabled=True,
        hidden=False,
    )
    async def redis_cinfo_cmd(self, ctx: commands.Context) -> None:
        """
        Show complex info about our Redis DB
        """
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

    @redis_group.command(
        name="showall",
        description="""Show all keys and data""",
        help="""Show all keys and data""",
        brief="Show all keys and data",
        aliases=["sa"],
        enabled=True,
        hidden=False,
    )
    async def redis_showall_cmd(self, ctx: commands.Context) -> None:
        """
        Show all data
        """
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
    async def redis_updater(self) -> None:
        """
        Automatically update redis lul
        """
        await self.bot.redis.set("updater", "0")
        await self.bot.redis.set("updater", "1")


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Databases(bot))
