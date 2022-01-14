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

    @commands.command(
        name="ban",
        description="""Ban a user from this guild""",
        help="""More help""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(1.0, 3.0, commands.BucketType.user)
    async def ban_user(self, ctx, user: discord.Member = None, *, reason: str = None):
        """Ban a member because they were being mean"""
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

        elif user.id == 889672871620780082:
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


def setup(bot):
    bot.add_cog(Mod(bot))
