import math
import sys
import traceback

import discord
import discord.utils
from colorama import Fore, Style
from discord.ext import commands
from gears import style


def log_error(error: str) -> None:
    """
    Logs an error string from an error string
    """
    print(f"{Fore.WHITE}[ {Fore.RED}ERROR {Fore.WHITE}] {Fore.RED}{error}")


class Errors(commands.Cog):
    """
    Handling all our bots errors
    """

    COLOR = style.Color.RED
    ICON = style.Emojis.REGULAR.cancel

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init the error handler
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
            if cog._get_overridden_method(cog.cog_command_error):
                return
        ignored_errors = (commands.CommandNotFound,)

        error = getattr(error, "original", error)

        if isinstance(error, ignored_errors):
            return

        # Discord Errors
        elif isinstance(error, discord.LoginFailure):
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )
            log_error("Failed to login.")

        elif isinstance(error, discord.Forbidden):
            embed = discord.Embed(
                title=f"Error - Missing Permissions",
                description=f"""I don't have permission to perform this action.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)

        elif isinstance(error, discord.NotFound):
            embed = discord.Embed(
                title=f"Error - Not Found",
                description=f"""I couldn't find the requested resource.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)

        # Catching all other http related errors
        elif isinstance(error, discord.HTTPException):
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )
            log_error(
                f"HTTP request failed. HTTP Code: {error.status} Discord Code: {error.code}"
            )

        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="Member Not Found",
                description=f"""`{error.argument}` was not found""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.ConversionError):
            pass

        elif isinstance(error, commands.MissingRequiredArgument):
            missing_argument = discord.Embed(
                title="Error",
                description=f"""{ctx.command}
                Parameter: {str(error.param).split(":", maxsplit=1)[0]}""",
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
                description=f"""{error.args}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.BadInviteArgument):
            pass

        elif isinstance(error, commands.CheckFailure):
            pass

        # Printing all errors out we need to know what happened, add an else when prod finally hits
        # All other Errors not returned come here. And we can just print the default TraceBack.
        print(f"Ignoring exception in command {ctx.command}:", file=sys.stderr)
        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Errors(bot))
