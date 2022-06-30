import discord
from discord.ext import commands
from gears import style, util


HELP_FORMAT = f"{util.ansi('grey')}prefix{util.ansi('white', None, 'bold')}command_name {util.ansi('white', None, 'bold')}<{util.ansi('blue', None, 'underline')}Required{util.ansi('white', None, 'bold')}>{util.ansi('clear')} {util.ansi('white', None, 'bold')}[{util.ansi('pink', None, 'underline')}Optional{util.ansi('white', None, 'bold')}]"


class BennyHelp(commands.HelpCommand):
    """
    Custom Help Command Class
    """

    def get_command_signature(self, command: commands.Command) -> str:
        """
        Rewriting the get_command_signature method to remove stuff I don't like
        """
        parent = command.parent
        entries = []
        while parent is not None:
            if not parent.signature or parent.invoke_without_command:
                entries.append(parent.name)
            else:
                entries.append(parent.name + " " + parent.signature)
            parent = parent.parent
        parent_sig = " ".join(reversed(entries))

        command_name = (
            command.name if not parent_sig else parent_sig + " " + command.name
        )

        return f"{self.context.clean_prefix}{command_name} {command.signature}"

    def get_colored_command_signature(self, command: commands.Command) -> str:
        """
        ANSI colored version
        """
        parent = command.parent
        entries = []
        while parent is not None:
            if not parent.signature or parent.invoke_without_command:
                entries.append(parent.name)
            else:
                entries.append(parent.name + " " + parent.signature)
            parent = parent.parent
        parent_sig = " ".join(reversed(entries))

        command_name = (
            command.name if not parent_sig else parent_sig + " " + command.name
        )

        colored_prefix = f"{util.ansi('grey')}{self.context.clean_prefix}"
        colored_command_name = (
            f"{util.ansi('white', None, 'bold')}{command_name}{util.ansi('reset')}"
        )
        colored_signature = (
            command.signature.replace(
                "[",
                f"{util.ansi('white', None, 'bold')}[{util.ansi('pink', None, 'underline')}",
            )
            .replace("]", f"{util.ansi('white', None, 'bold')}]{util.ansi('reset')}")
            .replace(
                "<",
                f"{util.ansi('white', None, 'bold')}<{util.ansi('blue', None, 'underline')}",
            )
            .replace(">", f"{util.ansi('white', None, 'bold')}>{util.ansi('reset')}")
        )

        return f"{colored_prefix}{colored_command_name} {colored_signature}"

    async def send_bot_help(self, mapping: dict) -> None:
        """When help is ran on its own no args"""
        embed = discord.Embed(title="Help", color=style.Color.AQUA)
        for cog, commands in mapping.items():
            command_signatures = []

            for command in commands:
                command_signatures.append(self.get_command_signature(command))

            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "ERROR")
                if cog_name in ["Errors", "Dev", "Events", "ERROR", "Help"]:
                    pass
                else:
                    embed.add_field(
                        name=f"{cog.ICON} {cog_name}",
                        value="not done yet",
                        inline=True,
                    )

        embed.set_author(
            name=f"{self.context.author.name}#{self.context.author.discriminator}",
            icon_url=self.context.author.avatar,
        )

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        """
        Sending help for cogs
        """
        embed = discord.Embed(
            title=cog.qualified_name,
            description=cog.description,
            color=cog.COLOR,
        )
        commands_view = ""
        for command in cog.get_commands():
            commands_view += f"\n{command}"
        embed.add_field(name="Commands", value=commands_view, inline=False)
        embed.set_author(
            name=f"{self.context.author.name}#{self.context.author.discriminator}",
            icon_url=self.context.author.avatar,
        )
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_group_help(self, group: commands.Group) -> None:
        """
        Sending help for groups
        """
        embed = discord.Embed(
            title=group.signature,
            description=f"""{group.short_doc}""",
            color=group.cog.COLOR,
        )
        for command in group.walk_commands():
            embed.add_field(
                name=self.get_command_signature(command),
                value=command.brief,
                inline=False,
            )
        embed.set_author(
            name=f"{self.context.author.name}#{self.context.author.discriminator}",
            icon_url=self.context.author.avatar,
        )
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command: commands.Command) -> None:
        """
        Sending help for actual commands
        """
        alias = command.aliases
        if alias:
            alias_text = ", ".join(alias)
        else:
            alias_text = "No Aliases"
        embed = discord.Embed(
            title=self.get_command_signature(command),
            description=f"""{command.help}
```ansi
{util.ansi('red', None, 'bold', 'underline')}Usage{util.ansi('clear')}
{HELP_FORMAT}
{self.get_colored_command_signature(command)}

{util.ansi('red', None, 'bold', 'underline')}Aliases{util.ansi('clear')}
{util.ansi('cyan', None, 'underline')}{alias_text}
```""",
            color=command.cog.COLOR,
        )
        embed.set_author(
            name=f"{self.context.author.name}#{self.context.author.discriminator}",
            icon_url=self.context.author.avatar,
        )

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_error_message(self, error: str) -> None:
        """
        Error Messages that may appear
        """
        embed = discord.Embed(title="Error", description=error, color=style.Color.RED)
        channel = self.get_destination()
        await channel.send(embed=embed)


class Help(commands.Cog):
    """
    The help cog
    """
    
    COLOR = style.Color.AQUA
    ICON = ":blue_book:"

    def __init__(self, bot: commands.Bot):
        """
        Init the help cog
        """
        self.bot = bot
        help_command = BennyHelp()
        help_command.cog = self
        bot.help_command = help_command

    @commands.command()
    async def show_help(self, ctx: commands.Context, hello: str, stuff, optional=None):
        await ctx.send_help(ctx.command.name)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
