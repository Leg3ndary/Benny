import asyncio
import random
import time

import asqlite
import discord
import discord.utils
import bTagScript as tse
from discord.ext import commands
from gears import style
from .tblocks import DeleteBlock


def is_a_nerd():
    async def predicate(ctx: commands.Context):
        return ctx.guild.id == 907096656732913744 or ctx.author.id == 360061101477724170
    return commands.check(predicate)

def guild_check(custom_tags: dict) -> bool:
    """
    Guild check for custom_tags
    """

    def predicate(ctx: commands.Context):
        """
        Predicate
        """
        return custom_tags.get(
            ctx.command.qualified_name
        ) and str(ctx.guild.id) in custom_tags.get(ctx.command.qualified_name)

    return commands.check(predicate)


def to_seed(ctx: commands.Context) -> dict:
    """
    Grab seed from context
    """
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

    def __init__(
        self,
        tag_id: str,
        guild: str,
        name: str,
        creator: str,
        created_at: str,
        uses: int,
        tagscript: str,
    ) -> None:
        """
        tag_id: str
            The tag id
        guild: str
            The guild id
        name: str
            The tag name
        creator: str
            Tags creator
        created_at: str
            Unix time tag was created at
        uses: int
            How many times the tag's been used
        tagscript: str
            The tagscript
        """
        self.tag_id = tag_id
        self.guild = guild
        self.name = name
        self.creator = creator
        self.created_at = created_at
        self.uses = uses
        self.tagscript = tagscript


class Tags(commands.Cog):
    """Tag cog"""

    custom_tags = {}

    def __init__(self, bot: commands.Bot):
        """
        Init the bot with all the blocks it needs
        """
        self.bot = bot
        bot.custom_tags = self.custom_tags
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
            tse.block.URLDecodeBlock(),
            tse.block.RequireBlock(),
            tse.block.BlacklistBlock(),
            tse.block.CommandBlock(),
            tse.block.OverrideBlock(),
            tse.block.RedirectBlock(),
            tse.block.CooldownBlock()
        ]
        externals = [
            DeleteBlock()
        ]
        self.tsei = tse.interpreter.AsyncInterpreter(blocks=tse_blocks + externals)

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
            );
        """
        )

        async with self.db.cursor() as cursor:
            row = await cursor.execute("""SELECT MAX(tag_id) FROM tags;""")
            _max = tuple(await row.fetchone())[0]
            if _max:
                self.latest_tag = int(_max)
            else: 
                self.latest_tag = 0

        await self.bot.blogger.load(f"Loaded tags up to {self.latest_tag}")

    async def cog_unload(self) -> None:
        """
        On cog unload close our db
        """
        await self.db.close()

    @commands.Cog.listener()
    async def on_initiate_all_tags(self) -> None:
        """
        Initiate all tags.
        """
        start = time.monotonic()
        async with self.db.cursor() as cursor:
            row = await cursor.execute("""SELECT * FROM tags;""")
            tags = tuple(await row.fetchall())
            for tag in tags:
                tag = tuple(tag)
                tag_mod = Tag(tag[0], tag[1], tag[2], tag[3], tag[4], tag[5], tag[6])
                await self.create_tag(tag_mod)

        end = time.monotonic()

        total_load = (round((end - start) * 1000, 2)) / 1000
        await self.bot.blogger.load(f"Loaded {self.latest_tag} tags in {total_load} seconds.")

    async def create_tag(self, tag: Tag) -> None:
        """
        Initiate a tag by adding it to the bot and everything
        """
        existing_command = self.custom_tags.get(tag.name)

        if not existing_command and self.bot.get_command(tag.name):
            raise commands.BadArgument(
                "Not sure how you got here... This shouldn't happen, a command already exists internally in the bot"
            )

        if existing_command:
            self.custom_tags[tag.name][tag.guild] = tag

        else:
            @commands.command(
                name=tag.name,
                help=f"Custom command: Outputs your custom provided output",
            )
            @guild_check(self.custom_tags)
            async def custom_tag_cmd(ctx: commands.Context, *, args: str = None) -> None:
                """
                Custom command
                """
                _tag = self.custom_tags[ctx.invoked_with][tag.guild]
                await self.invoke_custom_command(ctx, args, _tag)

            self.bot.add_command(custom_tag_cmd)
            self.custom_tags[tag.name] = {tag.guild: tag}

    async def remove_tag(self, tag: Tag) -> None:
        """
        Officially delete the tag.
        """
        if tag.name not in self.custom_tags or tag.guild not in self.custom_tags[tag.name]:
            raise commands.BadArgument(f"There isn't a custom tag called {self.name}")

        else:
            del self.custom_tags[tag.name][tag.guild]
            await self.db.execute("""DELETE FROM tags WHERE tag_id = ?;""", (tag.tag_id,))
            await self.db.commit()

    async def invoke_custom_command(
        self, ctx: commands.Context, args, tag: Tag
    ) -> None:
        """
        Invoke a custom command
        """
        seeds = {}
        if args:
            seeds.update({"args": tse.StringAdapter(args)})
        seeds.update(to_seed(ctx))

        tag.uses += 1

        await self.db.execute("""UPDATE tags SET uses = ? WHERE tag_id = ?;""", (tag.uses, tag.tag_id))
        await self.db.commit()

        response = await self.tsei.process(message=tag.tagscript, seed_variables=seeds)

        await ctx.send(response.body)

        if response.actions:
            for action, value in response.actions.items():
                if action == "delete" and value:
                    await ctx.message.delete()

    @commands.command(
        name="tt",
        description="""Description of command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=["playground", "tagtest", "testtag"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    @is_a_nerd()
    async def tt_cmd(self, ctx: commands.Context, *, args: str) -> None:
        """
        Testing out tags because yea...
        """
        seeds = {"args": tse.StringAdapter(args)}
        seeds.update(to_seed(ctx))

        response = await self.tsei.process(message=args, seed_variables=seeds)

        await ctx.send(response.body)

        if response.actions:
            for action, value in response.actions.items():
                if action == "delete" and value:
                    await ctx.message.delete()

    @commands.hybrid_group(
        name="tag",
        description="""Tag group""",
        help="""Anything to do with tags""",
        brief="Anything to do with tags",
        aliases=[],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def tag_group(self, ctx: commands.Context) -> None:
        """tag group"""
        if not ctx.invoked_subcommand:
            pass

    @tag_group.command(
        name="create",
        description="""Create a new tag""",
        help="""Create a new tag""",
        brief="Create a new tag",
        aliases=["add", "+"],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def tag_create_cmd(self, ctx: commands.Context, name: str, *, content: str) -> None:
        """
        Create a new tag
        """
        guild_tags = self.custom_tags.get(name.lower())
        tag = None
        if guild_tags:
            tag = guild_tags.get(str(ctx.guild.id))
        
        if tag:
            await self.db.execute("""UPDATE tags SET tagscript = ? WHERE tag_id = ?;""", (content, tag.tag_id))
            await self.db.commit()
            embed = discord.Embed(
                title=f"Success",
                description=f"""Edited tag `{name}`, new length `{len(content)}`""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREEN
            )
            await ctx.send(embed=embed)
        else:
            self.latest_tag += 1
            tag_data = (self.latest_tag, str(ctx.guild.id), name, str(ctx.author.id), round(time.time()), 0, content)

            await self.db.execute("""INSERT INTO tags VALUES(?, ?, ?, ?, ?, ?, ?);""", tag_data)
            await self.db.commit()
    
            tag_mod = Tag(tag_data[0], tag_data[1], tag_data[2], tag_data[3], tag_data[4], tag_data[5], tag_data[6])
            await self.create_tag(tag_mod)
            
            embed = discord.Embed(
                title=f"Success",
                description=f"""Created tag `{name}`, length `{len(content)}`""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREEN
            )
            await ctx.send(embed=embed)

    @tag_group.command(
        name="remove",
        description="""Delete a tag""",
        help="""Delete a tag""",
        brief="Delete a tag",
        aliases=["delete", "-"],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def tag_remove_cmd(self, ctx: commands.Context, name: str) -> None:
        """Delete a tag"""
        guild_commands = self.custom_tags.get(name.lower())
        if guild_commands:
            tag = guild_commands.get(str(ctx.guild.id))
            if tag:
                await self.remove_tag(tag)
                embed = discord.Embed(
                    title=f"Success",
                    description=f"""Removed tag `{name.lower()}`""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.RED
                )
                await ctx.send(embed=embed)

    @commands.command(
        name="list",
        description="""Description of command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def my_command(self, ctx: commands.Context) -> None:
        """Command description"""

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tags(bot))
