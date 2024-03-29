import math
import sys
import traceback
from typing import Union

import discord
import discord.utils
from colorama import Fore, Style
from discord.ext import commands
from gears import style
from gears.music_exceptions import NotConnected, NothingPlaying, QueueEmpty, QueueFull


def log_error(error: str) -> None:
    """
    Logs an error string from an error string
    """
    print(f"{Fore.WHITE}[ {Fore.RED}ERROR {Fore.WHITE}] {Fore.RED}{error}")


class ColoredView(discord.ui.View):
    """
    Colored View thingy
    """

    def __init__(self, normal: discord.Embed, color: discord.Embed) -> None:
        """
        Provide 2 different views

        Color and normal, will be able to switch between them
        """
        super().__init__()
        self.normal = normal
        self.color = color

    @discord.ui.button(label="Color", style=discord.ButtonStyle.blurple)
    async def on_color(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """
        switch to colored
        """
        await interaction.edit_original_message(embed=self.color)

    @discord.ui.button(label="Normal", style=discord.ButtonStyle.grey)
    async def on_normal(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """
        switch to normal
        """
        await interaction.edit_original_message(embed=self.normal)


class Errors(commands.Cog):
    """
    Handling all our bots errors
    """

    COLOR = style.Color.RED
    ICON = style.Emoji.REGULAR.cancel

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init the error handler
        """
        self.bot = bot

    async def handle_ac_errors(
        self,
        context: Union[commands.Context, discord.Interaction],
        error: Union[commands.CommandError, discord.app_commands.AppCommandError],
    ) -> None:
        """
        Handle app command errors
        """

        if hasattr(context.command, "on_error"):
            return

        cog = context.command.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error):
                return
        ignored_errors = (commands.CommandNotFound,)

        if isinstance(error, commands.CommandError):
            error = getattr(error, "original", error)
        else:
            # error = error
            pass

        _traceback = None
        embed = None
        person = (
            context.author if isinstance(context, commands.Context) else context.user
        )

        if isinstance(error, ignored_errors):
            return

        # Discord Errors

        elif isinstance(error, discord.LoginFailure):
            _traceback = True
            log_error("Failed to login.")
            self.bot.dispatch("log_critical", "Failed to login.")

        elif isinstance(error, discord.Forbidden):
            _traceback = False
            embed = discord.Embed(
                title="Error - Missing Permissions",
                description="""I don't have permission to perform this action.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            self.bot.dispatch(
                "log_debug",
                f"[ FORBIDDEN ] HTTP request failed. HTTP Code: {error.status} Discord Code: {error.code}",
            )

        elif isinstance(error, discord.NotFound):
            _traceback = False
            embed = discord.Embed(
                title="Error - Not Found",
                description="""I couldn't find the requested resource.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            self.bot.dispatch(
                "log_debug",
                f"[ NOT FOUND ] HTTP request failed. HTTP Code: {error.status} Discord Code: {error.code}",
            )

        elif isinstance(error, discord.DiscordServerError):
            _traceback = False
            embed = discord.Embed(
                title="Error - Discord",
                description="""Discords failing to work. Please be patient, and monitor their website [here](https://discordstatus.com/).""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            log_error("Encountered a 500 error from discord.")
            self.bot.dispatch(
                "log_critical",
                f"[ DISCORD 500 ] HTTP request failed. HTTP Code: {error.status} Discord Code: {error.code}",
            )

        # Catching all other HTTP related errors
        elif isinstance(error, discord.HTTPException):
            _traceback = True
            log_error(
                f"HTTP request failed. HTTP Code: {error.status} Discord Code: {error.code}"
            )
            self.bot.dispatch(
                "log_debug",
                f"[ HTTP FAIL ] HTTP request failed. HTTP Code: {error.status} Discord Code: {error.code}",
            )

        elif isinstance(error, discord.InvalidData):
            _traceback = True
            embed = discord.Embed(
                title="Error - Invalid Data",
                description="""Discord seems to be returning invalid data, please be patient and try again.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            log_error("Invalid data received from discord.")
            self.bot.dispatch(
                "log_error", "[ INVALID DATA ] Received invalid data from discord."
            )

        elif isinstance(error, discord.GatewayNotFound):
            _traceback = True
            log_error("Discord Gateway Not Found.")
            self.bot.dispatch(
                "log_critical", "[ GATEWAY NOT FOUND ] Discord Gateway not found."
            )

        elif isinstance(error, discord.ConnectionClosed):
            _traceback = True
            log_error(
                f"Websocket Connection closed, Reason: {error.reason} (Code: {error.code} Shard: {error.shard_id if not error.shard_id else '0'})."
            )
            self.bot.dispatch(
                "log_critical", "[ CONNECTION CLOSED ] Discord connection closed."
            )

        elif isinstance(error, discord.PrivilegedIntentsRequired):
            _traceback = True
            log_error(
                f"Missing privileged intents. (Shard {error.shard_id if not error.shard_id else '0'})"
            )
            self.bot.dispatch(
                "log_critical", "[ PRIVILEGED INTENTS ] Discord connection closed."
            )

        elif isinstance(error, discord.InteractionResponded):
            _traceback = True
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
            log_error(
                f"[ INTERACTION RESPONDED ] Interaction type {interstr} already responded to {error.interaction.guild.name} ({error.interaction.guild.id})"
            )
            self.bot.dispatch(
                "log_warn",
                f"[ INTERACTION RESPONDED ] Interaction type {interstr} already responded to {error.interaction.guild.name} ({error.interaction.guild.id})",
            )

        # Majority of these will be caused by user, these are commands ext errors
        elif isinstance(error, commands.ConversionError):
            _traceback = False
            embed = discord.Embed(
                title="Error - Conversion",
                description="""I attempted to convert the provided value, but failed.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )

        elif isinstance(error, commands.MissingRequiredArgument):
            _traceback = False
            parent = context.command.parent
            entries = []
            while parent is not None:
                if not parent.signature or parent.invoke_without_command:
                    entries.append(parent.name)
                else:
                    entries.append(parent.name + " " + parent.signature)
                parent = parent.parent
            parent_sig = " ".join(reversed(entries))

            command_name = (
                context.command.name
                if not parent_sig
                else parent_sig + " " + context.command.name
            )
            cleaned_prefix = (
                context.clean_prefix if isinstance(context, commands.Context) else "/"
            )
            command_format = (
                f"{cleaned_prefix}{command_name} {context.command.signature}"
            )

            colored_prefix = f"{Fore.BLACK}{cleaned_prefix}"
            colored_command_name = f"{command_name}{Fore.WHITE}"
            colored_signature = (
                context.command.signature.replace(
                    "[",
                    f"{Fore.WHITE}[{Fore.GREEN}",
                )
                .replace("]", f"{Fore.WHITE}]")
                .replace(
                    "<",
                    f"{Fore.WHITE}<{Fore.GREEN}",
                )
                .replace(">", f"{Fore.WHITE}>")
                .replace(
                    f"{Fore.WHITE}<{Fore.GREEN}{error.param.name}{Fore.WHITE}>",
                    f"{Fore.WHITE}<{Fore.RED}{error.param.name}{Fore.WHITE}>",
                )
            )

            colored = f"{colored_prefix}{colored_command_name} {colored_signature}{Style.RESET_ALL}"

            index = command_format.find(f"<{error.param.name}>")

            color = discord.Embed(
                title="Error - Missing Argument",
                description=f"""```ansi
{colored}
{" " * index}{Fore.RED}{"^" * int(len(error.param.name) + 2)}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            normal = discord.Embed(
                title="Error - Missing Argument",
                description=f"""```
{command_format}
{" " * index}{"^" * int(len(error.param.name) + 2)}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            if isinstance(context, commands.Context):
                await context.send(embed=color, view=ColoredView(normal, color))
            else:
                await context.response.send_message(
                    embed=color, view=ColoredView(normal, color)
                )

        elif isinstance(error, commands.MemberNotFound):
            _traceback = False
            embed = discord.Embed(
                title="Member Not Found",
                description=f"""`{error.argument}` was not found""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )

        elif isinstance(error, commands.DisabledCommand):
            _traceback = False
            embed = discord.Embed(
                title="Command Disabled",
                description=f"""{context.command} is disabled""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )

        elif isinstance(error, commands.NoPrivateMessage):
            _traceback = False
            try:
                await person.send(
                    f"{context.command} can not be used in Private Messages."
                )
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.ChannelNotFound):
            _traceback = False
            embed = discord.Embed(
                title="Error",
                description=f"""Channel `{error.argument}` was not found""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            embed.set_thumbnail(url=style.Emoji.IMAGE.cancel)

        elif isinstance(error, commands.CommandOnCooldown):
            _traceback = False
            embed = discord.Embed(
                title=f"{context.command} is on Cooldown",
                description=f"Please retry this command in {math.ceil(error.retry_after)} seconds",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )

        elif isinstance(error, commands.BadArgument):
            _traceback = False
            embed = discord.Embed(
                title="Error - Bad Argument",
                description=f"""{error.args[0]}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )

        elif isinstance(error, commands.BadInviteArgument):
            pass

        elif isinstance(error, commands.CheckFailure):
            pass

        elif isinstance(error, commands.CommandInvokeError):
            _traceback = False
            embed = discord.Embed(
                title="Error - Command Invoke",
                description=f"""{error.original}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )

        elif isinstance(error, QueueFull):
            _traceback = False
            embed = discord.Embed(
                title="Error - Queue Full",
                description="""The queue is currently full.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )

        elif isinstance(error, QueueEmpty):
            _traceback = False
            embed = discord.Embed(
                title="Error - Queue Empty",
                description="""The queue is currently empty.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )

        elif isinstance(error, NothingPlaying):
            _traceback = False
            embed = discord.Embed(
                title="Error - Nothing Playing",
                description="""Nothing is currently playing.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )

        elif isinstance(error, NotConnected):
            _traceback = False
            embed = discord.Embed(
                title="Error - Nothing Connected",
                description="""You need to be connected to a voice channel.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )

        # Printing all errors out we need to know what happened, add an else when prod finally hits
        # All other Errors not returned come here. And we can just print the default TraceBack.
        if _traceback or _traceback is None:
            print(f"Ignoring exception in command {context.command}:", file=sys.stderr)
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )
        if embed:
            if isinstance(context, commands.Context):
                await context.reply(embed=embed)
            else:
                await context.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_send_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ) -> None:
        """
        Send an error message for app commands
        """
        if isinstance(error, discord.app_commands.AppCommandNotFound):
            return
        if isinstance(
            error,
            (
                discord.app_commands.AppCommandError,
                discord.app_commands.AppCommandInvokeError,
            ),
        ):
            await self.handle_ac_errors(interaction, error)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        """
        The event triggered when an error is raised while invoking a command.
        """
        if isinstance(error, commands.CommandNotFound):
            return
        await self.handle_ac_errors(ctx, error)


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Errors(bot))
