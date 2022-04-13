import asqlite
import datetime
import discord
import discord.utils
import re
from discord.ext import commands
from gears import style


class Mod(commands.Cog):
    """Moderation related commands"""

    def __init__(self, bot):
        self.bot = bot

        '''
        name="command",
        description="""Description of command, complete overview with all neccessary info""",
        help="""More help""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False
        '''

    async def cog_load(self) -> None:
        """
        Load our sqlite db yay
        """
        # Warns
        self.db = await asqlite.connect("Databases/mod.db")
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS warns (
                id    TEXT    NOT NULL
                            PRIMARY KEY,
                mod  TEXT    NOT NULL,
                reason  TEXT,
                time  DATE    NOT NULL
            );
            """
        )
        await self.bot.printer.print_load("Mod")

    async def cog_unload(self) -> None:
        """
        Unload our sqlite db
        """
        await self.db.close()

    @commands.command(
        name="warn",
        description="""Warn a user""",
        help="""Warn a user, optional reason""",
        brief="Warn a user",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 7.0, commands.BucketType.user)
    async def warn_cmd(
        self, ctx, member: commands.Greedy[discord.Member], *, reason="None"
    ):
        """
        Warn cmd
        """
        await self.db.execute(
            f"""INSERT INTO warns VALUES(?, ?, ?, ?);""",
            (member.id, ctx.author.id, reason, datetime.datetime.now()),
        )
        await self.db.commit()
        embed = discord.Embed(
            title=f"Warned",
            description=f"""""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("yellow"),
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="ban",
        description="""Ban a user from this guild""",
        help="""More help""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 6.0, commands.BucketType.user)
    @commands.has_permissions(ban_members=True)
    async def ban_cmd(self, ctx, user: discord.Member = None, *, reason: str = None):
        """
        Ban a member, requires ban member permissionw3w
        """
        if user == ctx.author:
            same_user_embed = discord.Embed(
                title=f"Error",
                description=f"""You cannot ban yourself!""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            return await ctx.send(embed=same_user_embed)

        elif not user and re.match(r"[0-9]{15,19}", str(user)):
            try:
                user = await self.bot.fetch_user(int(user))
            except:
                pass

        elif not user:
            none_mentioned = discord.Embed(
                title=f"Error",
                description=f"""The user {user} was not found""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            return await ctx.send(embed=none_mentioned)

        elif user.id == self.bot.user.id:
            ban_bot = discord.Embed(
                title=f"Rude",
                description=f"""After all I've done for you, you try to ban me?""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("yellow"),
            )
            return await ctx.send(embed=ban_bot)
        else:
            try:
                user_reason = f"Banned by {ctx.author}: "
                if not reason:
                    reason = user_reason + "No Reason Specified"
                else:
                    reason = user_reason + reason
                await user.ban(reason=reason)
                banned_embed = discord.Embed(
                    title=f"Banned {user}",
                    description=f"""```diff
- {reason} -
```""",
                    timestamp=discord.utils.utcnow(),
                    color=style.get_color("green"),
                )
                return await ctx.send(embed=banned_embed)

            except Exception as e:
                error = discord.Embed(
                    title=f"Error",
                    description=f"""```diff
- {e}
```""",
                    timestamp=discord.utils.utcnow(),
                    color=style.get_color("red"),
                )
                await ctx.send(embed=error)

    @commands.command(
        name="unban",
        description="""Unban a user using an id""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 6.0, commands.BucketType.user)
    @commands.has_permissions(ban_members=True)
    async def unban_cmd(self, ctx, member: int, reason: str = None):
        """Command description"""
        if not re.match(r"[0-9]{15,19}", str(member)):
            embed = discord.Embed(
                title=f"Error",
                description=f"""Sorry but `{member}` doesn't seem to be a valid id.""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            return await ctx.send(embed=embed)
        try:
            member = await ctx.guild.fetch_ban(discord.Object(id=member))
        except discord.NotFound:
            embed = discord.Embed(
                title=f"Not Banned",
                description=f"""This user doesn't seem to be banned...""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("yellow"),
            )
            return await ctx.send(embed=embed)

        reason = f"Unbanned by: "

        await ctx.guild.unban(discord.Object(id=member), reason)

    @commands.group(name="modlogs")
    async def modlogs(self, ctx):
        """Check someones latest modlogs"""
        if not ctx.invoked_subcommand:
            pass

    @modlogs.command(name="channel", aliases=["set"])
    async def modlogs_channel(self, ctx, channel: discord.TextChannel):
        """Set a channel for modlogs"""

        data = await self.db_modlogs.find_one({"_id": ctx.guild.id})

        if not data:
            document = {
                "_id": ctx.guild.id,
                "channel": channel.id,
            }
            await self.db_modlogs.insert_one(document)

            modlogs_set = discord.Embed(
                title=f"Success",
                description=f"""Modlogs channel set to {channel.mention}""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("green"),
            )
            modlogs_set.set_thumbnail(url=style.get_emoji("image", "check"))
            await ctx.send(embed=modlogs_set)

        if data.get("channel") == channel.id:
            same_thing = discord.Embed(
                title=f"Error",
                description=f"""Modlogs channel is already set to {channel.mention}""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("yellow"),
            )
            await ctx.send(embed=same_thing)

        else:
            await self.db_modlogs.update_one(
                {"_id": ctx.guild.id}, {"$set": {"channel": channel.id}}
            )

            modlogs_changed = discord.Embed(
                title=f"Success",
                description=f"""Modlogs channel changed to {channel.mention}""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("green"),
            )
            modlogs_changed.set_thumbnail(url=style.get_emoji("image", "check"))
            await ctx.send(embed=modlogs_changed)

    @commands.Cog.listener()
    async def on_send_modlog(self, type, modlog):
        """Send modlogs to the specified channel if not just return"""
        pass


async def setup(bot):
    await bot.add_cog(Mod(bot))
