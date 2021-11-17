import discord
import traceback
import sys
from discord.ext import commands
from gears.style import c_get_color, c_get_emoji
import discord.utils
from gears.useful import report_error


class Errors(commands.Cog):
    """Handling all our bots errors"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        Parameters
        ------------
        ctx: commands.Context
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.
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

        if isinstance(error, commands.ConversionError):
            url = self.bot.dispatch(
                "create_error_pastebin", "ConversionError", ctx.message.id, error
            )

            conversion_error = discord.Embed(
                title=f"Error",
                description=f"""This error has been reported to the dev successfully.
Please do not spam this command as it will now likely not work.
```yaml
Error ID: {ctx.message.id}
Type: {error.converter}
```""",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("red"),
            )
            conversion_error.set_thumbnail(url=await c_get_emoji("image", "cancel"))
            await report_error(
                self.bot,
                f"""
[Error Report]({url})
```yaml
Error ID: {ctx.message.id}
Type: {error.converter}
```""",
            )
            await ctx.send(embed=conversion_error)

        elif isinstance(error, commands.MissingRequiredArgument):
            missing_argument = discord.Embed(
                title=f"Error",
                description=f"""Missing parameter:
```md
[Command](Error)
[{ctx.command}]({str(error.param).split(":")[0]})
```""",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("red"),
            )
            missing_argument.set_thumbnail(url=await c_get_emoji("image", "cancel"))
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
            if ctx.command.qualified_name == "modlogs channel":
                no_channel = discord.Embed(
                    title=f"Error",
                    description=f"""Channel `{error.argument}` was not found""",
                    timestamp=discord.utils.utcnow(),
                    color=await c_get_color("red"),
                )
                no_channel.set_thumbnail(url=await c_get_emoji("image", "cancel"))
                return await ctx.send(embed=no_channel)

        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title=f"{ctx.command} is on Cooldown",
                description=f"""Please retry this command after {error.retry_after}""",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("red"),
            )
            return await ctx.send(embed=embed)

        elif isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == "tag list":
                await ctx.send("I could not find that member. Please try again.")

            elif ctx.command.qualified_name == "":
                embed = discord.Embed(
                    title=f"",
                    description=f"""""",
                    timestamp=discord.utils.utcnow(),
                    color=await c_get_color(),
                )
                await ctx.send(embed=embed)

            else:
                embed = discord.Embed(
                    title=f"Not found",
                    description=f"""Conversion Error""",
                    timestamp=discord.utils.utcnow(),
                    color=await c_get_color("red"),
                )
                await ctx.send(embed=embed)

        elif isinstance(error, commands.BadInviteArgument):
            pass

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            print(
                "Ignoring exception in command {}:".format(ctx.command), file=sys.stderr
            )
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )


def setup(bot):
    bot.add_cog(Errors(bot))
