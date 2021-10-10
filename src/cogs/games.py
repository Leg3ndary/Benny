import discord
from discord.ext import commands 
from discord_slash.utils.manage_components import create_button, create_actionrow, ComponentContext, wait_for_component
from discord_slash.model import ButtonStyle
import datetime
from gears.style import c_get_color, c_get_emoji
import asyncio

class Games(commands.Cog):
    """Games to play with the bot"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ttt")
    async def tic_tac_toe(self, ctx, user: discord.Member = None):
        """A tic tac toe game to play with a friend."""
        if not user:
            failed1 = discord.Embed(
                title="You need to challenge someone!",
                description=f"""Add a descrip here""",
                timestamp=datetime.datetime.utcnow(),
                color=await c_get_color("red")
            )
            return await ctx.send(embed=failed1, delete_after=10.0)
        
        elif ctx.author == user:
            failed2 = discord.Embed(
                title="You cannot challenge yourself!",
                description=f"""add another descrip here""",
                timestamp=datetime.datetime.utcnow(),
                color=await c_get_color("red")
            )
            return await ctx.send(embed=failed2, delete_after=10.0)
        
        else:
            confirmation = [
                create_button(style=ButtonStyle.green, emoji=self.bot.get_emoji(873657241876705300), label="Accept"),
                create_button(style=ButtonStyle.red, emoji=self.bot.get_emoji(873659861395718227), label="Deny")
            ]
            row = create_actionrow(*confirmation)

            confirmation_embed = discord.Embed(
                title="Tic Tac Toe",
                description=f"""```diff
--- {ctx.author} challenged {user} ---
You have 30 seconds to respond to this Challenge!
```""",
                timestamp=datetime.datetime.utcnow(),
                color=await c_get_color("gray")
            )
            challenge_embed = await ctx.send(embed=confirmation_embed, components=[row])

            def check(bctx: ComponentContext):
                """A quick check to determine if the challenged person has actually responded"""
                return True
                if not bctx.author == user.id:
                    return False
                else:
                    return True 

            finished = [
                create_button(style=ButtonStyle.green, emoji=self.bot.get_emoji(873657241876705300), label="Accept", disabled=True),
                create_button(style=ButtonStyle.red, emoji=self.bot.get_emoji(873659861395718227), label="Deny", disabled=True)
            ]
            f_row = create_actionrow(*finished)
            try:
                bctx: ComponentContext = await wait_for_component(self.bot, components=row, check=check, timeout=30.0)
                await bctx.edit_origin(components=[f_row])

            except asyncio.TimeoutError:
                timeout_embed = discord.Embed(
                    title=f"Tic Tac Toe",
                    description=f"""```diff
--- {ctx.author} challenged {user} ---
- Challenge has timed out -
```""",
                    timestamp=datetime.datetime.utcnow(),
                    color=await c_get_color("red")
                )
                return await challenge_embed.edit(embed=timeout_embed, components=[f_row])

            accepted_embed = discord.Embed(
                title=f"Tic Tac Toe",
                description=f"""```diff
--- {ctx.author} challenged {user} ---
+ Challenge has been accepted, match starting in 3 seconds +
```""",
                timestamp=datetime.datetime.utcnow(),
                color=await c_get_color("red")
            )
            await challenge_embed.edit(embed=accepted_embed, components=[f_row])

            await asyncio.sleep(3)

            buttons1 = [
                create_button(style=ButtonStyle.gray, label=" - "),
                create_button(style=ButtonStyle.gray, label=" - "),
                create_button(style=ButtonStyle.gray, label=" - ")
            ]
            buttons2 = [
                create_button(style=ButtonStyle.gray, label=" - "),
                create_button(style=ButtonStyle.gray, label=" - "),
                create_button(style=ButtonStyle.gray, label=" - ")
            ]
            buttons3 = [
                create_button(style=ButtonStyle.gray, label=" - "),
                create_button(style=ButtonStyle.gray, label=" - "),
                create_button(style=ButtonStyle.gray, label=" - ")
            ]

            row1 = create_actionrow(*buttons1)
            row2 = create_actionrow(*buttons2)
            row3 = create_actionrow(*buttons3)
            
            game_embed = discord.Embed(
                title=f"{ctx.author} VS {user}",
                description=f"""""",
                timestamp=datetime.datetime.utcnow(),
                color=user.color
            )
            await ctx.send(embed=game_embed)

            game = await ctx.send(embed=game_embed, components=[row1, row2, row3])

def setup(bot):
    bot.add_cog(Games(bot))