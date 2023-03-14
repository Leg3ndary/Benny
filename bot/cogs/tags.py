import asyncio
import time
from typing import Any, Dict, List, Union

import asqlite
import bTagScript as tse
import discord
import discord.utils
from discord.ext import commands
from gears import style
from gears.database import BennyDatabases

FAKE_SEED = {
    "user": None,
    "target": None,
    "channel": None,
    "server": None,
    "args": None,
}


def clean(text: str) -> str:
    """
    Quickly clean a string
    """
    if text:
        return text.replace("\\", "\\\\").replace("`", "\\`")
    return ""


def guild_check(custom_tags: dict) -> bool:
    """
    Guild check for custom_tags
    """

    def predicate(ctx: commands.Context) -> bool:
        """
        Predicate
        """
        return custom_tags.get(ctx.command.qualified_name) and str(
            ctx.guild.id
        ) in custom_tags.get(ctx.command.qualified_name)

    return commands.check(predicate)


def to_seed(ctx: commands.Context) -> dict:
    """
    Grab seed from context return
    """
    user = tse.MemberAdapter(ctx.author)
    target = (
        tse.MemberAdapter(ctx.message.mentions[0]) if ctx.message.mentions else user
    )
    channel = tse.ChannelAdapter(ctx.channel)
    seed = {
        "user": user,
        "target": target,
        "channel": channel,
    }
    if ctx.guild:
        guild = tse.GuildAdapter(ctx.guild)
        seed.update(server=guild)
    return seed


class Tag:
    """
    Tag class
    """

    __slots__ = (
        "tag_id",
        "guild",
        "name",
        "creator",
        "created_at",
        "uses",
        "tagscript",
    )

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
    """
    Tag cog
    """

    COLOR = style.Color.ORANGE
    ICON = "<:_:992082395748634724>"

    custom_tags: dict = {}
    latest_tag: int = None

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init the bot with all the blocks the bot needs
        """
        self.bot = bot
        self.databases: BennyDatabases = bot.databases
        bot.custom_tags = self.custom_tags
        tse_blocks = [
            tse.block.BreakBlock(),
            tse.block.CommentBlock(),
            tse.block.AllBlock(),
            tse.block.AnyBlock(),
            tse.block.IfBlock(),
            tse.block.CountBlock(),
            tse.block.LengthBlock(),
            tse.block.BlacklistBlock(),
            tse.block.CommandBlock(),
            tse.block.CooldownBlock(),
            tse.block.DeleteBlock(),
            tse.block.EmbedBlock(),
            tse.block.OverrideBlock(),
            tse.block.ReactBlock(),
            tse.block.RedirectBlock(),
            tse.block.RequireBlock(),
            tse.block.MathBlock(),
            tse.block.OrdinalAbbreviationBlock(),
            tse.block.RandomBlock(),
            tse.block.RangeBlock(),
            tse.block.PythonBlock(),
            tse.block.ReplaceBlock(),
            tse.block.StopBlock(),
            tse.block.StrfBlock(),
            tse.block.URLDecodeBlock(),
            tse.block.URLEncodeBlock(),
            tse.block.DebugBlock(),
            tse.block.VarBlock(),
            tse.block.LooseVariableGetterBlock(),
        ]
        self.tsei = tse.interpreter.AsyncInterpreter(blocks=tse_blocks)
        self.channel_converter = commands.TextChannelConverter()
        self.member_converter = commands.MemberConverter()
        self.role_converter = commands.RoleConverter()

    async def cog_load(self) -> None:
        """
        On cog load start up our nice db
        """
        await self.databases.servers.execute(
            """
            CREATE TABLE IF NOT EXISTS tags_tags (
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
        await self.databases.servers.commit()

        async with self.databases.servers.cursor() as cursor:
            row = await cursor.execute("""SELECT MAX(tag_id) FROM tags_tags;""")
            _max = tuple(await row.fetchone())[0]
            if _max:
                self.latest_tag = int(_max)
            else:
                self.latest_tag = 0

        await self.bot.terminal.load(f"Loaded tags up to {self.latest_tag}")

    async def cog_unload(self) -> None:
        """
        On cog unload close our db
        """
        # await self.db.close()

    @commands.Cog.listener()
    async def on_initiate_all_tags(self) -> None:
        """
        Initiate all tags.
        """
        start = time.monotonic()
        async with self.databases.servers.cursor() as cursor:
            row = await cursor.execute("""SELECT * FROM tags_tags;""")
            tags = tuple(await row.fetchall())
            for tag in tags:
                tag = tuple(tag)
                tag_mod = Tag(tag[0], tag[1], tag[2], tag[3], tag[4], tag[5], tag[6])
                await self.create_tag(tag_mod)

        end = time.monotonic()

        total_load = (round((end - start) * 1000, 2)) / 1000
        await self.bot.terminal.load(
            f"Loaded {self.latest_tag} tags in {total_load} seconds."
        )

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
            self.custom_tags[tag.name] = {tag.guild: tag}
            self.latest_tag += 1

    async def remove_tag(self, tag: Tag) -> None:
        """
        Officially delete the tag.
        """
        if (
            tag.name not in self.custom_tags
            or tag.guild not in self.custom_tags[tag.name]
        ):
            raise commands.BadArgument(f"There isn't a custom tag called {self.name}")
        del self.custom_tags[tag.name][tag.guild]
        await self.databases.servers.execute(
            """DELETE FROM tags_tags WHERE tag_id = ?;""", (tag.tag_id,)
        )
        await self.databases.servers.commit()

    async def use_tag(self, tag: Tag) -> None:
        """
        Use a tag by adding to its counter
        """
        tag.uses += 1

        await asyncio.gather(
            self.databases.servers.execute(
                """UPDATE tags_tags SET uses = ? WHERE tag_id = ?;""",
                (tag.uses, tag.tag_id),
            ),
            self.databases.servers.commit(),
        )

    async def get_tags(self, guild: str) -> List[Tag]:
        """
        Get all a servers tags in a list

        Returns all of them as a Tag class
        """
        async with self.databases.servers.cursor() as cursor:
            tags_list = []
            row = await cursor.execute(
                """SELECT * FROM tags_tags WHERE guild = ?;""", (guild,)
            )
            tags = tuple(await row.fetchall())
            for tag in tags:
                tag = Tag(tag[0], tag[1], tag[2], tag[3], tag[4], tag[5], tag[6])
                tags_list.append(tag)
        return tags_list

    async def send_message(
        self,
        ctx: commands.Context,
        dest: Union[str, discord.TextChannel, bool],
        body: str,
        embeds: List[discord.Embed],
    ) -> None:
        """
        Send a message, should only used with invoke_custom_command
        """
        if not dest:
            await ctx.send(body if body else None, embeds=embeds)
        elif dest == "reply":
            await ctx.reply(body if body else None, embeds=embeds)
        else:
            await dest.send(body if body else None, embeds=embeds)

    async def handle_actions(
        self,
        actions: Dict[str, Any],
        ctx: commands.Context,
        embeds: List[discord.Embed],
    ) -> bool:
        """
        Handle a custom commands actions, returns if it can send
        """
        can_send = True
        for action, value in actions.items():
            if action == "delete" and value:
                await ctx.message.delete()
            elif action == "embed":
                embeds.append(value)
            elif action == "target":
                if value == "dm":
                    dest = ctx.author
                elif value == "reply":
                    dest = "reply"
                else:
                    dest = await self.channel_converter.convert(ctx, value)
                    if dest:
                        can_send = dest.permissions_for(ctx.author).send_messages
            elif action == "override":
                can_send = value.get("permissions")
            elif action == "requires":
                for i in action["items"]:
                    roles = []
                    channels = []
                    members = []
                    try:
                        roles.append(await self.role_converter.convert(ctx, i))
                    except commands.RoleNotFound:
                        try:
                            channels.append(
                                await self.channel_converter.convert(ctx, i)
                            )
                        except commands.ChannelNotFound:
                            try:
                                members.append(
                                    await self.member_converter.convert(ctx, i)
                                )
                            except commands.MemberNotFound:
                                pass

                send_require = True
                if roles:
                    if not any(role.id in ctx.author.roles for role in roles):
                        send_require = False
                        can_send = False
                if channels:
                    if ctx.channel not in channels:
                        send_require = False
                        can_send = False
                if members:
                    if not any(member.id in ctx.author.id for member in members):
                        send_require = False
                        can_send = False
                if send_require:
                    await ctx.send(action["response"])

            elif action == "blacklist":
                for i in action["items"]:
                    roles = []
                    channels = []
                    members = []
                    try:
                        roles.append(await self.role_converter.convert(ctx, i))
                    except commands.RoleNotFound:
                        try:
                            channels.append(
                                await self.channel_converter.convert(ctx, i)
                            )
                        except commands.ChannelNotFound:
                            try:
                                members.append(
                                    await self.member_converter.convert(ctx, i)
                                )
                            except commands.MemberNotFound:
                                pass

                send_blacklist = False
                if roles:
                    if any(role.id in ctx.author.roles for role in roles):
                        send_blacklist = True
                        can_send = False
                if channels:
                    if ctx.channel in channels:
                        send_blacklist = True
                        can_send = False
                if members:
                    if any(member.id in ctx.author.id for member in members):
                        send_blacklist = True
                        can_send = False
                if send_blacklist:
                    await ctx.send(action["response"])
        return can_send

    async def handle_debug(
        self,
        ctx: commands.Context,
        tag: Tag,
        debug: Dict[str, Any],
        embeds: List[discord.Embed],
        start: int,
        end: int,
    ) -> None:
        """
        Handle a custom commands debug, should only be used with invoke_custom_command
        """
        debug = ""
        defaults = ""

        debug.update(
            {
                "user": f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})",
                "target": f"{ctx.message.mentions[0].name}#{ctx.message.mentions[0].discriminator} ({ctx.message.mentions[0].id})"
                if ctx.message.mentions
                else f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})",
                "channel": f"{ctx.channel.name} ({ctx.channel.id})",
                "server": f"{ctx.guild.name} ({ctx.guild.id})",
            }
        )

        for k, v in debug.items():
            if k in FAKE_SEED:
                defaults += f"{clean(k)}: {clean(v)}\n"
            else:
                debug += f"{clean(k)}: {clean(v)}\n"

        debug_c = f"""```yaml
{debug.strip()}         
```"""
        defaults_c = f"""```yaml
{defaults.strip()}
```"""
        dembed = discord.Embed(
            title=f"{tag.name} Debug",
            description=f"""Tag Content Length: `{len(tag.tagscript)}`
            Time to Process: `{(round((end - start) * 1000, 5)) / 1000} seconds`""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.random(),
        )
        if debug:
            dembed.add_field(name="Debug Values", value=debug_c, inline=False)
        if defaults:
            dembed.add_field(name="Default Values", value=defaults_c, inline=False)
        embeds.append(dembed)

    async def invoke_custom_command(
        self, ctx: commands.Context, args: str, tag: Tag, use: bool
    ) -> None:
        """
        Invoke a custom command
        """
        if use:
            self.bot.loop.create_task(self.use_tag(tag))

        seeds = {}
        seeds.update({"args": tse.StringAdapter(args)})
        seeds.update(to_seed(ctx))

        start = time.monotonic()
        response = await self.tsei.process(message=tag.tagscript, seed_variables=seeds)
        end = time.monotonic()

        dest = None
        embeds = []
        can_send = True

        if response.actions:
            can_send = await self.handle_actions(response.actions, ctx, embeds)

        if response.extras.get("debug"):
            await self.handle_debug(
                ctx, tag, response.extras.get("debug"), embeds, start, end
            )

        if can_send:
            await self.send_message(ctx, dest, response.body, embeds)

    @commands.command(
        name="tagtest",
        description="""Test out tags in server without actually creating them.""",
        help="""Test out tags without actually creating one, and without using them in a server.""",
        brief="Test out tags",
        aliases=["playground", "tt", "testtag"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def tt_cmd(self, ctx: commands.Context, *, args: str) -> None:
        """
        Testing out tags because yea...
        """
        tag = Tag(0, 0, "", "", "", 0, args)
        await self.invoke_custom_command(ctx, args, tag, False)

    @commands.hybrid_group(
        name="tag",
        description="""Anything to do with tags.""",
        help="""Using this will display a help page for tags.""",
        brief="Help command group",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def tag_group(self, ctx: commands.Context) -> None:
        """
        Tag group
        """
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @tag_group.command(
        name="create",
        description="""Create a new tag in your server""",
        help="""Create a new tag""",
        brief="Create a new tag",
        aliases=["add", "+"],
        enabled=True,
        hidden=False,
    )
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def tag_create_cmd(
        self, ctx: commands.Context, name: str, *, content: str
    ) -> None:
        """
        Create a new tag
        """
        guild_tags = self.custom_tags.get(name)
        tag = None
        if guild_tags:
            tag = guild_tags.get(str(ctx.guild.id))

        for x in self.bot.commands:
            if x.name == name and name not in self.custom_tags:
                raise commands.BadArgument(
                    f"A command with the name {name} already exists. Please choose a different name."
                )

        if tag:
            await self.databases.servers.execute(
                """UPDATE tags_tags SET tagscript = ? WHERE tag_id = ?;""",
                (content, tag.tag_id),
            )
            await self.databases.servers.commit()
            new_tag = Tag(
                self.latest_tag,
                str(ctx.guild.id),
                name,
                tag.creator,
                round(time.time()),
                tag.uses,
                content,
            )
            guild_tags[str(ctx.guild.id)] = new_tag

            embed = discord.Embed(
                title="Success",
                description=f"""Edited tag `{name}`, new length `{len(content)}`""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREEN,
            )
            await ctx.send(embed=embed)

        else:
            self.latest_tag += 1
            tag_data = (
                self.latest_tag,
                str(ctx.guild.id),
                name,
                str(ctx.author.id),
                round(time.time()),
                0,
                content,
            )

            await self.databases.servers.execute(
                """INSERT INTO tags_tags VALUES(?, ?, ?, ?, ?, ?, ?);""", tag_data
            )
            await self.databases.servers.commit()

            tag_mod = Tag(
                tag_data[0],
                tag_data[1],
                tag_data[2],
                tag_data[3],
                tag_data[4],
                tag_data[5],
                tag_data[6],
            )
            await self.create_tag(tag_mod)

            embed = discord.Embed(
                title="Success",
                description=f"""Created tag `{name}`, length `{len(content)}`""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREEN,
            )
            await ctx.send(embed=embed)

    @tag_group.command(
        name="remove",
        description="""Delete a tag from your server""",
        help="""Delete a tag""",
        brief="Delete a tag",
        aliases=["delete", "-", "del"],
        enabled=True,
        hidden=False,
    )
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def tag_remove_cmd(self, ctx: commands.Context, name: str) -> None:
        """
        Delete a tag
        """
        commands_named = self.custom_tags.get(name.lower())

        if commands_named:
            tag = commands_named.get(str(ctx.guild.id))
            if tag:
                await self.remove_tag(tag)
                embed = discord.Embed(
                    title="Success",
                    description=f"""Removed tag `{name.lower()}`""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.RED,
                )
                await ctx.send(embed=embed)

    @tag_group.command(
        name="list",
        description="""List all of a servers tags""",
        help="""List all of a servers tags""",
        brief="List all of a servers tags",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 8.0, commands.BucketType.channel)
    async def tag_list_cmd(self, ctx: commands.Context) -> None:
        """
        Display all of a servers tags
        """
        tags = await self.get_tags(str(ctx.guild.id))

        vis_list = []

        for tag in tags:
            vis_list.append(
                f"{tag.name} - Uses: {tag.uses} Length: {len(tag.tagscript)}"
            )

        vis = "\n".join(vis_list)

        embed = discord.Embed(
            title=f"{ctx.guild.name} Tags",
            description=f"""```yaml
{vis.strip()}
            ```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.PINK,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Tags(bot))
