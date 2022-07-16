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

        _traceback = None
        embed = None

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
            parent = ctx.command.parent
            entries = []
            while parent is not None:
                if not parent.signature or parent.invoke_without_command:
                    entries.append(parent.name)
                else:
                    entries.append(parent.name + " " + parent.signature)
                parent = parent.parent
            parent_sig = " ".join(reversed(entries))

            command_name = (
                ctx.command.name
                if not parent_sig
                else parent_sig + " " + ctx.command.name
            )

            command_format = f"{ctx.clean_prefix}{command_name} {ctx.command.signature}"

            colored_prefix = f"{Fore.BLACK}{ctx.clean_prefix}"
            colored_command_name = f"{command_name}{Fore.WHITE}"
            colored_signature = (
                ctx.command.signature.replace(
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
            await ctx.send(embed=color, view=ColoredView(normal, color))

        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                title="Member Not Found",
                description=f"""`{error.argument}` was not found""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )

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
            embed = discord.Embed(
                title="Error",
                description=f"""Channel `{error.argument}` was not found""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            embed.set_thumbnail(url=style.Emoji.IMAGE.cancel)

        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title=f"{ctx.command} is on Cooldown",
                description=f"Please retry this command in {math.ceil(error.retry_after)} seconds",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )

        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Error - Bad Argument",
                description=f"""{error.args}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )

        elif isinstance(error, commands.BadInviteArgument):
            pass

        elif isinstance(error, commands.CheckFailure):
            pass

        # Printing all errors out we need to know what happened, add an else when prod finally hits
        # All other Errors not returned come here. And we can just print the default TraceBack.
        if _traceback or _traceback is None:
            print(f"Ignoring exception in command {ctx.command}:", file=sys.stderr)
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )

        if embed:
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Errors(bot))
