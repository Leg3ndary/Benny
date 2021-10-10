import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext  
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle

class Slash(commands.Cog):
    """Slash commands which have no real category"""
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(name="test")
    async def _test(self, ctx: SlashContext):
        embed = discord.Embed(
            title="Embed Test"
        )
        await ctx.send(embed=embed)

    @commands.command(name="hello")
    async def _testt(self, ctx):
        """testing"""
        buttons = [
            create_button(style=ButtonStyle.green, label="A green button"),
            create_button(style=ButtonStyle.blue, label="A blue button")
        ]
        action_row = create_actionrow(*buttons)

        await ctx.send("hello", components=[action_row]) 

def setup(bot):
    bot.add_cog(Slash(bot))