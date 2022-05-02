import discord
import discord.utils
import io
import os
import re
import textwrap
import traceback
from contextlib import redirect_stdout
from discord.ext import commands
from gears import style


async def cleanup_code(content: str) -> str:
    """
    Automatically removes code blocks from code
    """
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:-1])


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
            line_temp = re.sub("\+", f"[0;32m+", line, 1)
            line_temp = re.sub("(\+)(?!.*\+)", f"+[0;0m", line_temp)
            line_temp = re.sub("\-", f"[0;31m-", line_temp, 1)
            line_temp = re.sub("(\-)(?!.*\-)", f"-[0;0m", line_temp)

        temp.append(line_temp)

    return "\n".join(temp)


class Dev(commands.Cog):
    """
    All commands in this cog are owner only, they are meant for bot development
    """

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if the user is the owner."""
        return await self.bot.is_owner(ctx.author)

    @commands.group()
    async def dev(self, ctx):
        """Commands thats sole purpose is for me to experiment."""
        if not ctx.invoked_subcommand:
            embed = discord.Embed(
                title=f"{ctx.author.display_name} is the Dev",
                description=f"This message is only displayable by him.",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("black"),
            )
            await ctx.send(embed=embed)

    @dev.command(
        help="Load a cog",
        brief="Loading Cogs",
        description="None",
        hidden=True,
    )
    async def load(self, ctx, *, cog: str):
        try:
            await self.bot.load_extension(cog)
            await self.bot.printer.print_cog_update(cog, "LOAD")
        except Exception as e:
            embed_fail = discord.Embed(
                title=f"__{cog}__ Load Fail",
                description=f"""```diff
- {cog} loading failed
- Reason: {e}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color(),
            )
            return await ctx.send(embed=embed_fail)

        else:
            embed = discord.Embed(
                title=f"__{cog}__ Loaded",
                description=f"""```diff
+ {cog} loaded successfuly
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color(),
            )
            await ctx.send(embed=embed)

    @dev.command(
        help="Unload a cog",
        brief="Unloading Cogs",
        description="None",
        hidden=True,
    )
    async def unload(self, ctx, *, cog: str):
        try:
            await self.bot.unload_extension(cog)
            await self.bot.printer.print_cog_update(cog, "UNLOAD")
        except Exception as e:
            embed_fail = discord.Embed(
                title=f"__{cog}__ Unload Fail",
                description=f"""```diff
- {cog} unloading failed
- Reason: {e}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color(),
            )
            return await ctx.send(embed=embed_fail)

        else:
            embed = discord.Embed(
                title=f"__{cog}__ Unloaded",
                description=f"""```diff
+ {cog} unloaded successfully
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color(),
            )
            await ctx.send(embed=embed)

    @dev.command(
        help="Unload then Load a cog",
        brief="Reloading Cogs",
        description="None",
        hidden=True,
    )
    async def reload(self, ctx, *, cog: str):
        try:
            await self.bot.unload_extension(cog)
            await self.bot.load_extension(cog)
            await self.bot.printer.print_cog_update(cog, "RELOAD")
        except Exception as e:
            embed_fail = discord.Embed(
                title=f"__{cog}__ Reload Fail",
                description=f"""```diff
- {cog} reloading failed
- Reason: {e}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color(),
            )
            return await ctx.send(embed=embed_fail)

        else:
            embed = discord.Embed(
                title=f"__{cog}__ Reloaded",
                description=f"""```diff
+ {cog} reloaded successfully
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color(),
            )
            return await ctx.send(embed=embed)

    @dev.command(
        help="Shows a list of all servers that Tenshi is in.",
        brief="Servers List",
        description="None",
        hidden=True,
    )
    async def servers(self, ctx):
        servers = self.bot.guilds
        servers_var = ""
        for guild in servers:
            servers_var = f"{servers_var}\n{guild.name}"
        embed = discord.Embed(
            title=f"Tenshi Server List ============== {len(self.bot.guilds)}",
            description=f"""```
{servers_var}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color(),
        )
        await ctx.send(embed=embed)

    @dev.command(
        name="sync",
        description="""Runs git pull and syncs cogs""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    async def sync_cmd(self, ctx):
        cmd = os.popen("git pull").read()

        embed = discord.Embed(
            title=f"Git Pull",
            description=f"""```ansi
{await format_git_msg(cmd)}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("aqua"),
        )
        await ctx.send(embed=embed)
        cog_statuslist = []
        fails = 0
        success = 0
        for cog in self.bot.cog_list:
            try:
                await self.bot.unload_extension(cog)
                await self.bot.load_extension(cog)
                await self.bot.printer.print_cog_update(cog, "RELOAD")

            except Exception as e:
                cog_statuslist.append(f"- {cog} failed\n- {e}")
                fails += 1

            else:
                cog_statuslist.append(f"+ {cog} reloaded")
                success += 1

        if fails > 0:
            embed_color = style.get_color("red")
        else:
            embed_color = style.get_color("green")

        cog_visual = f"\n".join(cog_statuslist)

        embed = discord.Embed(
            title=f"{self.bot.user.name} Sync ============================",
            description=f"""```diff
{cog_visual}```
            `{success}` cogs have been reloaded.
            `{fails}` cogs have failed loading.""",
            timestamp=discord.utils.utcnow(),
            color=embed_color,
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="syncs",
        description="""Syncs slash commands""",
        help="""Syncs slash commands""",
        brief="Syncs slash commands",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    async def syncs_cmd(self, ctx):
        """
        Syncs the bots command tree
        """
        await self.bot.tree.sync()
        embed = discord.Embed(
            title=f"Tree Sync",
            description=f"""Bot sync has been completed""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("green")
        )
        await ctx.send(embed=embed)

    @dev.command(
        name="leave",
        description="""Leave a guild""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    async def leave_cmd(self, ctx, *, guild: discord.Guild):
        """Leave a guild."""
        try:
            await ctx.guild.leave()
            embed = discord.Embed(
                title=f"Left {guild.name}",
                description=f"""```md
- Owned by {guild.owner} - {guild.owner_id}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color(),
            )
            await ctx.send(embed=embed)

        except Exception as e:
            embed_error = discord.Embed(
                title="Error",
                description=f"""```diff
- {e}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            await ctx.send(embed=embed_error)

    @commands.command(
        name="eval",
        description="""Eval command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=["exec"],
        enabled=True,
        hidden=True,
    )
    async def eval_cmd(self, ctx, *, code: str):
        """Evaluates code given"""
        if "```py" not in code:
            no_cb = discord.Embed(
                title="Error",
                description="Include a code block dumb fuck",
                timestamp=discord.utils.utcnow(),
                color=style.get_color(),
            )
            return await ctx.send(embed=no_cb)

        env = {"bot": self.bot, "ctx": ctx}

        env.update(globals())

        code = await cleanup_code(code)
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
                color=style.get_color("red"),
            )
            print(f"{e.__class__.__name__}: {e}")
            return await ctx.send(embed=embed_e1)

        func = env["func"]

        try:
            with redirect_stdout(stdout):
                out = await func()

        except Exception as e:
            value = stdout.getvalue()
            embed_e2 = discord.Embed(
                title="Error",
                description=f"""```py
{value}{traceback.format_exc()}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            print(value + traceback.format_exc())
            return await ctx.send(embed=embed_e2)

        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction(style.get_emoji("regular", "check"))
            except:
                pass

            if out is None:
                if value:
                    evaluated = discord.Embed(
                        title="Evaluated",
                        description=f"""```py
{value}
```""",
                        timestamp=discord.utils.utcnow(),
                        color=style.get_color("green"),
                    )
                    return await ctx.send(embed=evaluated)

            else:
                embed_e3 = discord.Embed(
                    title="Error",
                    description=f"""```py
{value}{out}
```""",
                    timestamp=discord.utils.utcnow(),
                    color=style.get_color("red"),
                )
                print(value + out)
                return await ctx.send(embed=embed_e3)

    @dev.command(
        name="close",
        description="""Immediately stops the bot""",
        help="""Stop the bot immediately""",
        brief="""Stop the bot""",
        aliases=["end", "stop"],
        enabled=True,
        hidden=True,
    )
    async def end_bot(self, ctx):
        """Stopping the bot"""
        await ctx.message.add_reaction(style.get_emoji("regular", "check"))
        embed = discord.Embed(
            title=f"Shutting Down Bot",
            description=f"""```diff
Add stuff here later...
```""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("red"),
        )
        await ctx.send(embed=embed)
        await self.bot.close()


async def setup(bot):
    await bot.add_cog(Dev(bot))
