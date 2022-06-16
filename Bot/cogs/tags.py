import asyncio
import random

import asqlite
import discord
import discord.utils
import TagScriptEngine as tse
from discord.ext import commands
from gears import style


def to_seed(ctx: commands.Context) -> dict:
    """
    Grab seed from context"""
    author = tse.MemberAdapter(ctx.author)
    target = (
        tse.MemberAdapter(ctx.message.mentions[0]) if ctx.message.mentions else author
    )
    channel = tse.ChannelAdapter(ctx.channel)
    seed = {
        "author": author,
        "user": author,
        "target": target,
        "member": target,
        "channel": channel,
    }
    if ctx.guild:
        guild = tse.GuildAdapter(ctx.guild)
        seed.update(guild=guild, server=guild)
    return seed


class Tag:
    """
    Tag class
    """

    def __init__(self) -> None:
        pass


class Tags(commands.Cog):
    """Tag cog"""

    def __init__(self, bot: commands.Bot):
        """
        Init the bot with all the blocks it needs
        """
        self.bot = bot
        tse_blocks = [
            tse.block.MathBlock(),
            tse.block.RandomBlock(),
            tse.block.RangeBlock(),
            tse.block.AnyBlock(),
            tse.block.IfBlock(),
            tse.block.AllBlock(),
            tse.block.BreakBlock(),
            tse.block.StrfBlock(),
            tse.block.StopBlock(),
            tse.block.AssignmentBlock(),
            tse.block.FiftyFiftyBlock(),
            tse.block.ShortCutRedirectBlock("args"),
            tse.block.LooseVariableGetterBlock(),
            tse.block.SubstringBlock(),
            tse.block.EmbedBlock(),
            tse.block.ReplaceBlock(),
            tse.block.PythonBlock(),
            tse.block.URLEncodeBlock(),
            tse.block.RequireBlock(),
            tse.block.BlacklistBlock(),
            tse.block.CommandBlock(),
            tse.block.OverrideBlock(),
            tse.block.RedirectBlock(),
            tse.block.CooldownBlock(),
        ]
        self.tsei = tse.interpreter.AsyncInterpreter(blocks=tse_blocks)

    async def cog_load(self) -> None:
        """
        On cog load start up our nice db
        """
        self.db = await asqlite.connect("Databases/tags.db")

        await self.db.execute(
            """
        CREATE TABLE IF NOT EXISTS tags (
            tag_id     TEXT PRIMARY KEY
                            NOT NULL,
            guild      TEXT NOT NULL,
            name       TEXT NOT NULL,
            creator    TEXT NOT NULL,
            created_at TEXT NOT NULL,
            uses       INT  NOT NULL,
            tagscript  TEXT NOT NULL
        )
        """
        )

    @commands.command(
        name="tag",
        description="""Description of command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    @commands.is_owner()
    async def tag_cmd(self, ctx: commands.Context, *, args: str) -> None:
        """
        Testing out tags because yea...
        """
        seeds = {"args": tse.StringAdapter(args)}
        seeds.update(to_seed(ctx))

        await ctx.send(seeds)
        response = await self.tsei.process(message=args, seed_variables=seeds)

        await ctx.send(response.body)
        await ctx.send(f"{response.actions} + {response.variables}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tags(bot))
