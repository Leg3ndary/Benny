import asyncio
import time
from typing import List

import asqlite
import bTagScript as tse
import discord
import discord.utils
from discord.ext import commands
from gears import style


FAKE_SEED = {
    "user": None,
    "target": None,
    "channel": None,
    "server": None,
    "args": None
}


def is_a_nerd() -> bool:  # I think its bool
    """
    Check if this person is part of the nerd thingy for asty
    """

    async def predicate(ctx: commands.Context) -> bool:
        return ctx.guild.id == 907096656732913744 or ctx.author.id == 360061101477724170

    return commands.check(predicate)


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
    Grab seed from context
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

    __slots__ = ("tag_id", "guild", "name", "creator", "created_at", "uses", "tagscript")

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

    def __init__(self, bot: commands.Bot):
        """
        Init the bot with all the blocks the bot needs
        """
        self.bot = bot
        self.db: asqlite.Connection = None
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
            tse.block.LooseVariableGetterBlock()
        ]
        self.tsei = tse.interpreter.AsyncInterpreter(blocks=tse_blocks)
        self.channel_converter = commands.TextChannelConverter()
        self.member_converter = commands.MemberConverter()
        self.role_converter = commands.RoleConverter()

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
        await self.bot.blogger.load(
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

            '''
            @commands.command(
                name=tag.name,
                help="Custom command: Outputs your custom provided output",
            )
            @guild_check(self.custom_tags)
            async def custom_tag_cmd(
                ctx: commands.Context, *, args: str = None
            ) -> None:
                """
                Custom command
                """
                _tag = self.custom_tags[ctx.invoked_with][tag.guild]
                await self.invoke_custom_command(ctx, args, _tag, True)

            self.bot.add_command(custom_tag_cmd)
            '''
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

        else:
            del self.custom_tags[tag.name][tag.guild]
            await self.db.execute(
                """DELETE FROM tags WHERE tag_id = ?;""", (tag.tag_id,)
            )
            await self.db.commit()

    async def use_tag(self, tag: Tag) -> None:
        """
        Use a tag by adding to its counter
        """
        tag.uses += 1

        await asyncio.gather(
            self.db.execute(
                """UPDATE tags SET uses = ? WHERE tag_id = ?;""", (tag.uses, tag.tag_id)
            ),
            self.db.commit(),
        )

    async def get_tags(self, guild: str) -> List[Tag]:
        """
        Get all a servers tags in a list

        Returns all of them as a Tag class
        """
        async with self.db.cursor() as cursor:
            tags_list = []
            row = await cursor.execute(
                """SELECT * FROM tags WHERE guild = ?;""", (guild,)
            )
            tags = tuple(await row.fetchall())
            for tag in tags:
                tag = Tag(tag[0], tag[1], tag[2], tag[3], tag[4], tag[5], tag[6])
                tags_list.append(tag)
        return tags_list

    async def invoke_custom_command(
        self, ctx: commands.Context, args: str, tag: Tag, use: bool
    ) -> None:
        """
        Invoke a custom command
        """
        if use:
            self.bot.loop.create_task(self.use_tag(tag))

        seeds = {}
        if args:
            seeds.update({"args": tse.StringAdapter(args)})
        seeds.update(to_seed(ctx))

        start_process = time.monotonic()
        response = await self.tsei.process(message=tag.tagscript, seed_variables=seeds)
        end_process = time.monotonic()

        dest = None
        can_send = True
        embeds = []

        if response.actions:
            for action, value in response.actions.items():
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
                                channels.append(await self.channel_converter.convert(ctx, i))
                            except commands.ChannelNotFound:
                                try:
                                    members.append(await self.member_converter.convert(ctx, i))
                                except commands.MemberNotFound:
                                    pass

                    send_require = True
                    if roles:
                        if not any(
                            role.id in ctx.author.roles for role in roles
                        ):
                            send_require = False
                            can_send = False
                    if channels:
                        if ctx.channel not in channels:
                            send_require = False
                            can_send = False
                    if members:
                        if not any(
                            member.id in ctx.author.id for member in members
                        ):
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
                                channels.append(await self.channel_converter.convert(ctx, i))
                            except commands.ChannelNotFound:
                                try:
                                    members.append(await self.member_converter.convert(ctx, i))
                                except commands.MemberNotFound:
                                    pass

                    send_blacklist = False
                    if roles:
                        if any(
                            role.id in ctx.author.roles for role in roles
                        ):
                            send_blacklist = True
                            can_send = False
                    if channels:
                        if ctx.channel in channels:
                            send_blacklist = True
                            can_send = False
                    if members:
                        if any(
                            member.id in ctx.author.id for member in members
                        ):
                            send_blacklist = True
                            can_send = False
                    if send_blacklist:
                        await ctx.send(action["response"])

        if response.debug:
            debug = ""
            defaults = ""

            response.debug.update({
                "user": f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})",
                "target": f"{ctx.message.mentions[0].name}#{ctx.message.mentions[0].discriminator} ({ctx.message.mentions[0].id})" if ctx.message.mentions else f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})",
                "channel": f"{ctx.channel.name} ({ctx.channel.id})",
                "server": f"{ctx.guild.name} ({ctx.guild.id})",
            })

            for k, v in response.debug.items():
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
                Time to Process: `{(round((end_process - start_process) * 1000, 5)) / 1000} seconds`""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.random(),
            )
            if debug:
                dembed.add_field(name="Debug Values", value=debug_c, inline=False)
            if defaults:
                dembed.add_field(name="Default Values", value=defaults_c, inline=False)
            embeds.append(dembed)

        if can_send:
            if not dest:
                await ctx.send(response.body if response.body else None, embeds=embeds)
            elif dest == "reply":
                await ctx.reply(response.body if response.body else None, embeds=embeds)
            else:
                await dest.send(response.body if response.body else None, embeds=embeds)

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
        tag = Tag(0, 0, "", "", "", 0, args)
        await self.invoke_custom_command(ctx, args, tag, False)

    @commands.hybrid_group(
        name="tag",
        description="""Tag group""",
        help="""Anything to do with tags""",
        brief="Anything to do with tags",
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
        description="""Create a new tag""",
        help="""Create a new tag""",
        brief="Create a new tag",
        aliases=["add", "+"],
        enabled=True,
        hidden=False,
    )
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
            await self.db.execute(
                """UPDATE tags SET tagscript = ? WHERE tag_id = ?;""",
                (content, tag.tag_id),
            )
            await self.db.commit()
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

            await self.db.execute(
                """INSERT INTO tags VALUES(?, ?, ?, ?, ?, ?, ?);""", tag_data
            )
            await self.db.commit()

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
        description="""Delete a tag""",
        help="""Delete a tag""",
        brief="Delete a tag",
        aliases=["delete", "-"],
        enabled=True,
        hidden=False,
    )
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
    @commands.cooldown(1.0, 10.0, commands.BucketType.channel)
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
