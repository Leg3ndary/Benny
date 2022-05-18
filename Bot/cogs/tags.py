import TagScriptEngine as tse
import asyncio
import discord
import discord.utils
from discord.ext import commands
from gears import style


class Tags(commands.Cog):
    """Cog Example Description"""

    def __init__(self, bot):
        self.bot = bot
        tse_blocks = [
            tse.MathBlock(),
            tse.RandomBlock(),
            tse.RangeBlock(),
            tse.AnyBlock(),
            tse.IfBlock(),
            tse.AllBlock(),
            tse.BreakBlock(),
            tse.StrfBlock(),
            tse.StopBlock(),
            tse.AssignmentBlock(),
            tse.FiftyFiftyBlock(),
            tse.ShortCutRedirectBlock("args"),
            tse.LooseVariableGetterBlock(),
            tse.SubstringBlock(),
            tse.EmbedBlock(),
            tse.ReplaceBlock(),
            tse.PythonBlock(),
            tse.URLEncodeBlock(),
            tse.RequireBlock(),
            tse.BlacklistBlock(),
            tse.CommandBlock(),
            tse.OverrideBlock(),
            tse.RedirectBlock(),
            tse.CooldownBlock(),
        ]
        self.tsei = tse.interpreter.AsyncInterpreter(blocks=tse_blocks)

    @commands.command(
        name="tagtest",
        description="""Description of command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def tagtest_cmd(self, ctx: commands.Context, *, args):
        """"""
        response = await self.tsei.process(
            message=args, seed_variables={"args": tse.StringAdapter(args)}
        )

        await ctx.send(response.body)
        await ctx.send(response.actions)
        await ctx.send(response.variables)


async def setup(bot):
    await bot.add_cog(Tags(bot))
