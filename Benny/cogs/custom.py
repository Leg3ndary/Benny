import asyncio
import discord
import discord.utils
from discord import guild
from discord.ext import commands
from gears.msg_views import DeleteView
from gears.style import c_get_color, c_get_emoji


def is_tong_guild():
    def guild_check(ctx):
        return ctx.guild.id == 773026012631269406

    return commands.check(guild_check)


class CustomCommands(commands.Cog):
    """Custom commands that could be removed"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="bangurmom",
        description="""Whut""",
        help="""abcdefg""",
        brief="""ok""",
        usage="[Ping]",
        aliases=["angurmom"],
        enabled=True,
        hidden=True,
    )
    @commands.guild_only()
    @is_tong_guild()
    async def bangurmomthing(self, ctx):
        """Friend said he'd pay me shit to add this"""
        deleteview = DeleteView()
        if not ctx.message.mentions:
            deleteview.bctx = await ctx.send(
                f"id bang ur mom {ctx.author.mention}", view=deleteview
            )
        else:
            member = ctx.message.mentions[0]
            deleteview.bctx = await ctx.send(
                f"id bang ur mom {member.mention}", view=deleteview
            )

    @commands.command(
        name="bangurmommy", enabled=True, hidden=True, aliases=["angurmommy"]
    )
    @is_tong_guild()
    async def anotherweirdcommand(self, ctx):
        """Send a picture because... idk"""
        deleteview = DeleteView()
        deleteview.bctx = await ctx.send(
            "https://media.discordapp.net/attachments/839606979457450024/923705170553077840/9400DB00-2E69-49FC-B1BB-985496EA56C5.png?width=198&height=429",
            view=deleteview,
        )


def setup(bot):
    bot.add_cog(CustomCommands(bot))
