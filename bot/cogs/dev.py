import io
import os
import re
import textwrap
import traceback
from contextlib import redirect_stdout

import discord
import discord.utils
from discord.ext import commands, tasks
from gears import style
from redis import asyncio as aioredis


async def format_git_msg(content: str) -> str:
    """
    Format a git message to have git messages and look pretty
    """
    temp = []
    for line in content.split("\n"):
        if "Updating" in line:
            line_temp = line.replace("Update ", "")
            utemp = line.split("..")
            line_temp = f"[0;33m+Update [0;34m{utemp[0]}[0;37m..[0;34m{utemp[1]}"
        if "Fast-forward" == line:
            line_temp = line.replace("Fast-foward", "[0;35mFast-forward[0;0m")
        else:
            line_temp = re.sub(r"\+", "[0;32m+", line, 1)
            line_temp = re.sub(r"(\+)(?!.*\+)", "+[0;0m", line_temp)
            line_temp = re.sub(r"\-", "[0;31m-", line_temp, 1)
            line_temp = re.sub(r"(\-)(?!.*\-)", "-[0;0m", line_temp)

        temp.append(line_temp)

    return "\n".join(temp)


class Dev(commands.Cog):
    """
    All commands in this cog are owner only, they are meant for bot development
    """

    COLOR = style.Color.BLACK
    ICON = "<:_:992072492191592448>"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init for the bot
        """
        self.bot = bot
        self.redis_updater.start()

    async def cog_check(self, ctx: commands.Context) -> bool:
        """
        Check if the user is the owner.
        """
        return await self.bot.is_owner(ctx.author)

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

    async def cog_unload(self) -> None:
        """
        Stop task loop if cog unloaded
        """
        self.redis_updater.cancel()

    @commands.group(
        name="dev",
        description="""Commands thats sole purpose is for me to develop the bot.""",
        help="""Commands thats sole purpose is for me to develop the bot.""",
        brief="Commands thats sole purpose is for me to develop the bot.",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    async def dev_group(self, ctx: commands.Context) -> None:
        """
        Commands thats sole purpose is for me to develop the bot.
        """
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @dev_group.command(
        name="load",
        description="""Load a cog""",
        help="""Load a cog""",
        brief="Load a cog",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    async def load_cmd(self, ctx: commands.Context, *, cog: str) -> None:
        """
        Load a cog
        """
        try:
            await self.bot.load_extension(cog)
            await self.bot.blogger.cog_update(cog, "LOAD")
        except Exception as e:
            embed_fail = discord.Embed(
                title=f"__{cog}__ Load Fail",
                description=f"""```diff
- {cog} loading failed
- Reason: {e}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.random(),
            )
            await ctx.send(embed=embed_fail)

        else:
            embed = discord.Embed(
                title=f"__{cog}__ Loaded",
                description=f"""```diff
+ {cog} loaded successfuly
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.random(),
            )
            await ctx.send(embed=embed)

    @dev_group.command(
        name="unload",
        description="""Unload a cog""",
        help="""Unload a cog""",
        brief="Unload a cog",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    async def unload_cmd(self, ctx: commands.Context, *, cog: str) -> None:
        """
        Unload a cog
        """
        try:
            await self.bot.unload_extension(cog)
            await self.bot.blogger.cog_update(cog, "UNLOAD")

        except Exception as e:
            embed_fail = discord.Embed(
                title=f"__{cog}__ Unload Fail",
                description=f"""```diff
- {cog} unloading failed
- Reason: {e}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.random(),
            )
            await ctx.send(embed=embed_fail)

        else:
            embed = discord.Embed(
                title=f"__{cog}__ Unloaded",
                description=f"""```diff
+ {cog} unloaded successfully
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.random(),
            )
            await ctx.send(embed=embed)

    @dev_group.command(
        name="reload",
        description="""Reload a cog""",
        help="""Reload a cog""",
        brief="Reload a cog",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    async def reload_cmd(self, ctx: commands.Context, *, cog: str) -> None:
        """
        Reload a cog
        """
        try:
            await self.bot.unload_extension(cog)
            await self.bot.load_extension(cog)
            await self.bot.blogger.cog_update(cog, "RELOAD")
        except Exception as e:
            embed_fail = discord.Embed(
                title=f"__{cog}__ Reload Fail",
                description=f"""```diff
- {cog} reloading failed
- Reason: {e}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.random(),
            )
            await ctx.send(embed=embed_fail)

        else:
            embed = discord.Embed(
                title=f"__{cog}__ Reloaded",
                description=f"""```diff
+ {cog} reloaded successfully
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.random(),
            )
            await ctx.send(embed=embed)

    @dev_group.command(
        name="servers",
        description="""Show the bots servers""",
        help="""Show the bots servers""",
        brief="Show the bots servers",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    async def dev_servers_cmd(self, ctx: commands.Context) -> None:
        """
        Show every server the bots actually in
        """
        servers = self.bot.guilds
        servers_var = ""
        for guild in servers:
            servers_var += f"\n{guild.name}"
        embed = discord.Embed(
            title=f"{self.bot.user.name} Server List {len(self.bot.guilds)}",
            description=f"""```
{servers_var}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        await ctx.send(embed=embed)

    @dev_group.command(
        name="pull",
        description="""Run the git pull command for the bot""",
        help="""Run the git pull command for the bot""",
        brief="Run the git pull command for the bot",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    async def dev_pull_cmd(self, ctx: commands.Context) -> None:
        """
        Run the git pull command for the bot
        """
        cmd = os.popen("git pull").read()

        embed = discord.Embed(
            title="Git Pull",
            description=f"""```ansi
{await format_git_msg(cmd)}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        await ctx.send(embed=embed)

    @dev_group.command(
        name="sync",
        description="""Runs git pull and syncs all cogs""",
        help="""Runs git pull and syncs all cogs""",
        brief="Runs git pull and syncs all cogs",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    async def dev_sync_cmd(self, ctx: commands.Context) -> None:
        """
        Sync command

        Runs git pull and syncs all cogs
        """
        cmd = self.bot.get_command("dev pull")
        await cmd(ctx)

        cog_statuslist = []
        fails = 0
        success = 0
        for cog in self.bot.cog_list:
            try:
                await self.bot.unload_extension(cog)
                await self.bot.load_extension(cog)
                await self.bot.blogger.cog_update(cog, "RELOAD")

            except Exception as e:
                cog_statuslist.append(f"- {cog} failed\n- {e}")
                fails += 1

            else:
                cog_statuslist.append(f"+ {cog} reloaded")
                success += 1

        if fails > 0:
            embed_color = style.Color.RED
        else:
            embed_color = style.Color.GREEN

        cog_visual = "\n".join(cog_statuslist)

        embed = discord.Embed(
            title=f"{self.bot.user.name} Sync",
            description=f"""```diff
{cog_visual}```
            `{success}` cogs have been reloaded.
            `{fails}` cogs have failed loading.""",
            timestamp=discord.utils.utcnow(),
            color=embed_color,
        )
        await ctx.send(embed=embed)

    @dev_group.command(
        name="syncs",
        description="""Syncs slash commands""",
        help="""Syncs slash commands""",
        brief="Syncs slash commands",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    async def dev_syncs_cmd(self, ctx: commands.Context) -> None:
        """
        Syncs the bots command tree
        """
        await self.bot.tree.sync()
        embed = discord.Embed(
            title="Tree Sync",
            description="""Bot sync has been completed""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        await ctx.send(embed=embed)

    @dev_group.command(
        name="leave",
        description="""Leave a guild""",
        help="""Leave a guild""",
        brief="Leave a guild",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    async def dev_leave_cmd(
        self, ctx: commands.Context, *, guild: discord.Guild
    ) -> None:
        """
        Leave a guild.
        """
        await ctx.guild.leave()
        embed = discord.Embed(
            title=f"Left {guild.name}",
            description=f"""```md
- Owned by {guild.owner} - {guild.owner_id}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.random(),
        )
        await ctx.reply(embed=embed)

    @dev_group.command(
        name="clear",
        description="""Clears the bots slash commands""",
        help="""Clears the bots slash commands""",
        brief="Clears the bots slash commands",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    async def dev_clear_cmd(self, ctx: commands.Context) -> None:
        """
        Clears the bots slash commands
        """
        self.bot.tree.clear_commands(guild=None)
        await self.bot.tree.sync()
        embed = discord.Embed(
            title="Tree Clear",
            description="""Bot tree has been cleared""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        await ctx.reply(embed=embed)

    @commands.command(
        name="eval",
        description="""Eval command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=["exec"],
        enabled=True,
        hidden=True,
    )
    async def eval_cmd(self, ctx: commands.Context, *, code: str) -> None:
        """
        Evaluates code given, I stole this from r danny, ty rapptz...
        """
        env = {"bot": self.bot, "ctx": ctx}
        env.update(globals())

        if code.startswith("```") and code.endswith("```"):
            code = "\n".join(code.split("\n")[1:-1])
        stdout = io.StringIO()

        to_compile = f"""async def func():\n{textwrap.indent(code, "  ")}"""

        try:
            exec(to_compile, env)
        except Exception as e:
            embed_e1 = discord.Embed(
                title="Error",
                description=f"""```py
{e.__class__.__name__}: {e}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            print(f"{e.__class__.__name__}: {e}")
            await ctx.send(embed=embed_e1)
            return

        func = env["func"]

        try:
            with redirect_stdout(stdout):
                out = await func()

        except Exception:
            value = stdout.getvalue()
            embed_e2 = discord.Embed(
                title="Error",
                description=f"""```py
{value}{traceback.format_exc()}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            print(value + traceback.format_exc())
            await ctx.send(embed=embed_e2)

        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction(style.Emoji.REGULAR.check)
            except:
                pass

            if not out:
                if value:
                    evaluated = discord.Embed(
                        title="Evaluated",
                        description=f"""```py
{value}
```""",
                        timestamp=discord.utils.utcnow(),
                        color=style.Color.GREEN,
                    )
                    await ctx.send(embed=evaluated)

            else:
                embed_e3 = discord.Embed(
                    title="Error",
                    description=f"""```py
{value}{out}
```""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.RED,
                )
                print(value + out)
                await ctx.send(embed=embed_e3)

    @commands.command(
        name="openfile",
        description="""Opens and sends a file""",
        help="""Opens and sends a file""",
        brief="Opens and sends a file",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    async def open_file_cmd(self, ctx: commands.Context, filename: str) -> None:
        """
        Opens and sends a file
        """
        file = discord.File(filename)
        await ctx.send(f"Showing file: `{filename}`", file=file)

    @dev_group.command(
        name="close",
        description="""Immediately stops the bot""",
        help="""Stop the bot immediately""",
        brief="""Stop the bot""",
        aliases=["end", "stop"],
        enabled=True,
        hidden=True,
    )
    async def dev_close_cmd(self, ctx: commands.Context) -> None:
        """
        Stopping the bot
        """
        await ctx.message.add_reaction(style.Emoji.REGULAR.check)
        embed = discord.Embed(
            title="Shutting Down Bot",
            description="""```diff
Shutting down the bot...
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.RED,
        )
        await ctx.send(embed=embed)
        await self.bot.close()

    @commands.group(
        name="redis",
        description="""Redis Group""",
        help="""Redis Group""",
        brief="Redis Group",
        aliases=[],
        enabled=True,
        hidden=True,
    )
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

        await self.bot.redis.set("Key", "Data") Set a key
        value = await self.bot.redis.get("Key")
        """
        await self.bot.redis.set("updater", "0")
        await self.bot.redis.set("updater", "1")


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Dev(bot))
