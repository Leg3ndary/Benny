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

        traceback = None

        if isinstance(error, ignored_errors):
            return

        # Discord Errors

        elif isinstance(error, discord.LoginFailure):
            traceback = True
            log_error("Failed to login.")
            self.bot.dispatch("log_critical", f"Failed to login.")

        elif isinstance(error, discord.Forbidden):
            traceback = False
            embed = discord.Embed(
                title=f"Error - Missing Permissions",
                description=f"""I don't have permission to perform this action.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)
            self.bot.dispatch("log_debug", f"[ FORBIDDEN ] HTTP request failed. HTTP Code: {error.status} Discord Code: {error.code}")

        elif isinstance(error, discord.NotFound):
            traceback = False
            embed = discord.Embed(
                title=f"Error - Not Found",
                description=f"""I couldn't find the requested resource.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)
            self.bot.dispatch("log_debug", f"[ NOT FOUND ] HTTP request failed. HTTP Code: {error.status} Discord Code: {error.code}")

        elif isinstance(error, discord.DiscordServerError):
            traceback = False
            embed = discord.Embed(
                title=f"Error - Discord",
                description=f"""Discords failing to work. Please be patient, and monitor their website [here](https://discordstatus.com/).""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)
            log_error("Encountered a 500 error from discord.")
            self.bot.dispatch("log_critical", f"[ DISCORD 500 ] HTTP request failed. HTTP Code: {error.status} Discord Code: {error.code}")

        # Catching all other HTTP related errors
        elif isinstance(error, discord.HTTPException):
            traceback = True
            log_error(
                f"HTTP request failed. HTTP Code: {error.status} Discord Code: {error.code}"
            )
            self.bot.dispatch("log_debug", f"[ HTTP FAIL ] HTTP request failed. HTTP Code: {error.status} Discord Code: {error.code}")

        elif isinstance(error, discord.InvalidData):
            traceback = True
            embed = discord.Embed(
                title=f"Error - Invalid Data",
                description=f"""Discord seems to be returning invalid data, please be patient and try again.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)
            log_error(f"Invalid data received from discord.")
            self.bot.dispatch("log_error", f"[ INVALID DATA ] Received invalid data from discord.")

        elif isinstance(error, discord.GatewayNotFound):
            traceback = True
            log_error(f"Discord Gateway Not Found.")
            self.bot.dispatch("log_critical", f"[ GATEWAY NOT FOUND ] Discord Gateway not found.")

        elif isinstance(error, discord.ConnectionClosed):
            traceback = True
            log_error(f"Websocket Connection closed, Reason: {error.reason} (Code: {error.code} Shard: {error.shard_id if not error.shard_id else '0'}).")
            self.bot.dispatch("log_critical", f"[ CONNECTION CLOSED ] Discord connection closed.")

        elif isinstance(error, discord.PrivilegedIntentsRequired):
            traceback = True
            log_error(f"Missing privileged intents. (Shard {error.shard_id if not error.shard_id else '0'})")
            self.bot.dispatch("log_critical", f"[ PRIVILEGED INTENTS ] Discord connection closed.")

        elif isinstance(error, discord.InteractionResponded):
            traceback = True
            _type = error.interaction.type
            interstr = "Unknown"
            if _type == discord.InteractionType.ping:
                interstr = "Ping"
            elif _type == discord.InteractionType.application_command:
                interstr = "Slash Command"
            elif _type == discord.InteractionType.component:
                interstr = "Component"
            elif _type == discord.InteractionType.autocomplete:
                interstr = "Autocomplete"
            elif _type == discord.InteractionType.modal_submit:
                interstr = "Modal"
            log_error(f"[ INTERACTION RESPONDED ] Interaction type {interstr} already responded to {error.interaction.guild.name} ({error.interaction.guild.id})")
            self.bot.dispatch("log_warn", f"[ INTERACTION RESPONDED ] Interaction type {interstr} already responded to {error.interaction.guild.name} ({error.interaction.guild.id})")
        
        # Majority of these will be caused by user, these are commands ext errors
        elif isinstance(error, commands.ConversionError):
            traceback = False
            embed = discord.Embed(
                title=f"Error - Conversion",
                description=f"""I attempted to convert the provided value, but failed.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Error - Missing Argument",
                description=f"""You seem to be missing an argument!{ctx.command}
                Parameter: {str(error.param).split(":", maxsplit=1)[0]}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)

        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="Member Not Found",
                description=f"""`{error.argument}` was not found""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)

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
        if traceback or traceback is None:
            print(f"Ignoring exception in command {ctx.command}:", file=sys.stderr)
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Errors(bot))
