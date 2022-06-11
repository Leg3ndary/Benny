import math
import sys
import traceback

import discord
import discord.utils
from discord.ext import commands
from gears import style


class Errors(commands.Cog):
    """Handling all our bots errors"""

    def __init__(self, bot: commands.Bot) -> None:
        """
        init the thing
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        """
        The event triggered when an error is raised while invoking a command.

        Parameters
        ----------
        ctx: commands.Context
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.

        Returns
        -------
        None
        """
        if hasattr(ctx.command, "on_error"):
            return

        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return
        ignored = (commands.CommandNotFound,)

        error = getattr(error, "original", error)

        if isinstance(error, ignored):
            return

        if isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="Member Not Found",
                description=f"""The member {error.argument} was not found""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.ConversionError):
            # unfinished
            pass

        elif isinstance(error, commands.MissingRequiredArgument):
            missing_argument = discord.Embed(
                title="Error",
                description=f"""Missing parameter:
```md
Command Error
[{ctx.command}]({str(error.param).split(":", maxsplit=1)[0]})
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            missing_argument.set_thumbnail(url=style.Emojis.IMAGE.cancel)
            await ctx.send(embed=missing_argument)

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(f"{ctx.command} has been disabled.")

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(
                    f"{ctx.command} can not be used in Private Messages."
                )
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.ChannelNotFound):
            no_channel = discord.Embed(
                title="Error",
                description=f"""Channel `{error.argument}` was not found""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            no_channel.set_thumbnail(url=style.Emojis.IMAGE.cancel)
            await ctx.send(embed=no_channel)

        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title=f"{ctx.command} is on Cooldown",
                description=f"Please retry this command in {math.ceil(error.retry_after)} seconds",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Not found",
                description=f"""{error.with_traceback}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.BadInviteArgument):
            pass

        elif isinstance(error, commands.CheckFailure):
            print(error)

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            print(f"Ignoring exception in command {ctx.command}:", file=sys.stderr)
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Errors(bot))
