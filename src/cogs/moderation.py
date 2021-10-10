import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType 
from discord_slash.utils.manage_components import create_button, create_actionrow, ComponentContext, wait_for_component
from discord_slash.model import ButtonStyle
import datetime
from gears.style import c_get_color, c_get_emoji
import asyncio

class Moderation(commands.Cog):
    """Moderation related commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="ban"
    )
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(1.0, 3.0, commands.BucketType.user)
    async def _ban(self, ctx, user: discord.Member = None, *, reason: str = None):
        """Ban a member because they were being mean"""
        if user == ctx.author:
            same_user_embed = discord.Embed(
                title=f"Error",
                description=f"""You cannot ban yourself!""",
                timestamp=datetime.datetime.utcnow(),
                color=await c_get_color("red")
            )
            return await ctx.send(embed=same_user_embed)
        elif not user:
            none_mentioned = discord.Embed(
                title=f"Error",
                description=f"""The user {user} was not found""",
                timestamp=datetime.datetime.utcnow(),
                color=await c_get_color("red")
            )
            return await ctx.send(embed=none_mentioned)
        elif user.id == 889672871620780082:
            ban_bot = discord.Embed(
                title=f"Rude",
                description=f"""After all I've done for you, you try to ban me?""",
                timestamp=datetime.datetime.utcnow(),
                color=await c_get_color("yellow")
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
                    timestamp=datetime.datetime.utcnow(),
                    color=await c_get_color("green")
                )
                return await ctx.send(embed=banned_embed)

            except Exception as e:
                error = discord.Embed(
                    title=f"Error",
                    description=f"""```diff
- {e}
```""",
                    timestamp=datetime.datetime.utcnow(),
                    color=await c_get_color("red")
                )
                await ctx.send(embed=error)

def setup(bot):
    bot.add_cog(Moderation(bot))