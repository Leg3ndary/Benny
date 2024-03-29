from typing import List, Mapping, Optional

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
        ANSI colored version of help
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

    async def send_bot_help(
        self, mapping: Mapping[Optional[commands.Cog], List[commands.Command]]
    ) -> None:
        """
        When help is ran on its own no args
        """
        embed = discord.Embed(
            title="Benny Help",
            description=f"""Welcome to Benny's Help Page, find information and help about all of Benny's commands here!
            
            Benny currently has {len(self.context.bot.commands)} commands, and {len(self.context.bot.cogs)} cogs loaded.""",
            color=style.Color.AQUA,
            timestamp=discord.utils.utcnow(),
        )

        view = BotHelpView(self, mapping)

        embed.set_author(
            name=f"{self.context.author.name}#{self.context.author.discriminator}",
            icon_url=self.context.author.avatar,
        )

        channel = self.get_destination()
        await channel.send(embed=embed, view=view)

    async def send_cog_help(self, cog: commands.Cog) -> None:
        """
        Sending help for cogs
        """
        embed = discord.Embed(
            title=cog.qualified_name,
            description=cog.description,
            color=cog.COLOR,
        )
        cog_commands = []
        for command in cog.get_commands():
            if isinstance(command, commands.HybridCommand):
                cog_commands.append(f"`{command.name}` - {command.brief}")
            elif isinstance(command, commands.HybridGroup):
                cog_commands.append(f"`{command.name}` - {command.brief}")
            else:
                cog_commands.append(f"`{command.name}` - {command.brief}")
        embed.add_field(name="Commands", value="\n".join(cog_commands), inline=False)
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


class BotHelpSelect(discord.ui.Select):
    """
    A select menu for the help command
    """

    def __init__(
        self,
        help_command: BennyHelp,
        mapping: Mapping[Optional[commands.Cog], List[commands.Command]],
    ) -> None:
        """
        Construct the help select menu
        """
        self.help_command = help_command
        super().__init__(placeholder="Select a Category")
        for cog, _commands in mapping.items():
            command_signatures = []

            for command in _commands:
                command_signatures.append(help_command.get_command_signature(command))

            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "ERROR")
                if cog_name not in ("Errors", "Dev", "Events", "ERROR", "Help"):
                    self.add_option(
                        label=cog_name,
                        description=cog.description,
                        value=cog_name,
                        emoji=cog.ICON,
                    )

    async def callback(self, interaction: discord.Interaction):
        """
        Callback for the select menu
        """
        cog = self.help_command.context.bot.get_cog(self.values[0])

        embed = discord.Embed(
            title=cog.qualified_name,
            description=cog.description,
            color=cog.COLOR,
        )
        cog_commands = []
        for command in cog.get_commands():
            if isinstance(command, commands.HybridCommand):
                cog_commands.append(f"`{command.name}` - {command.brief}")
            elif isinstance(command, commands.HybridGroup):
                cog_commands.append(f"`{command.name}` - {command.brief}")
            else:
                cog_commands.append(f"`{command.name}` - {command.brief}")
        embed.add_field(name="Commands", value="\n".join(cog_commands), inline=False)
        embed.set_author(
            name=f"{self.help_command.context.author.name}#{self.help_command.context.author.discriminator}",
            icon_url=self.help_command.context.author.avatar,
        )

        new_view = discord.ui.View()
        new_view.add_item(self)
        new_view.add_item(CogHelpSelect(self.help_command, cog))

        await interaction.response.edit_message(embed=embed, view=new_view)


class BotHelpView(discord.ui.View):
    """
    A help view for the bot
    """

    def __init__(
        self,
        help_command: BennyHelp,
        mapping: Mapping[Optional[commands.Cog], List[commands.Command]],
    ) -> None:
        """
        Construct the help view
        """
        super().__init__()
        self.add_item(BotHelpSelect(help_command, mapping))


class CogHelpSelect(discord.ui.Select):
    """
    A select menu for the cog help command
    """

    def __init__(self, help_command: commands.HelpCommand, cog: commands.Cog) -> None:
        """
        Construct the cog help select menu
        """
        super().__init__(placeholder="Select a Command")
        for command in cog.get_commands():
            self.add_option(
                label=command.name,
                description=command.brief,
                value=command.name,
            )
        self.help_command = help_command
        self.cog = cog

    async def callback(self, interaction: discord.Interaction) -> None:
        """
        Change the embed to a nice help view
        """
        await interaction.response.defer()
        for command in self.cog.get_commands():
            if command.name == self.values[0]:
                alias = command.aliases
                if alias:
                    alias_text = ", ".join(alias)
                else:
                    alias_text = "No Aliases"
                embed = discord.Embed(
                    title=self.help_command.get_command_signature(command),
                    description=f"""{command.help}
```ansi
{util.ansi('red', None, 'bold', 'underline')}Usage{util.ansi('clear')}
{HELP_FORMAT}
{self.help_command.get_colored_command_signature(command)}

{util.ansi('red', None, 'bold', 'underline')}Aliases{util.ansi('clear')}
{util.ansi('cyan', None, 'underline')}{alias_text}
```""",
                    color=command.cog.COLOR,
                )
                embed.set_author(
                    name=f"{self.help_command.context.author.name}#{self.help_command.context.author.discriminator}",
                    icon_url=self.help_command.context.author.avatar,
                )
                await interaction.edit_original_response(embed=embed)
                break


class Help(commands.Cog):
    """
    The help cog
    """

    COLOR = style.Color.AQUA
    ICON = "📘"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init the help cog
        """
        self.bot = bot
        help_command = BennyHelp()
        help_command.cog = self
        bot.help_command = help_command

    @discord.app_commands.command(name="help", description="Get help for the bot")
    async def help_cmd(self, interaction: discord.Interaction) -> None:
        """
        Slash help command
        """
        embed = discord.Embed(
            title="Sorry!",
            description="""The bot currently does not have a slash help command, while this is subject to change, please use the regular text help command for now.""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.RED,
        )
        await interaction.response.send_message(embed=embed)

    # @discord.app_commands.command(
    #     name="help",
    #     description="Get help on a command or cog",
    # )
    # async def help_cmd(
    #     self, interaction: discord.Interaction, command: Optional[str]
    # ) -> None:
    #     """
    #     Slash help command
    #     """
    #     await interaction.response.defer()
    #     ctx = await self.bot.get_context(interaction, cls=commands.Context)
    #     if command is not None:
    #         await ctx.send_help(command)
    #     else:
    #         await ctx.send_help()

    # @help_cmd.autocomplete("command")
    # async def command_autocomplete(
    #     self, interaction: discord.Interaction, needle: str
    # ) -> List[discord.app_commands.Choice[str]]:
    #     """
    #     Slash help command autocomplete
    #     """
    #     assert self.bot.help_command
    #     ctx = await self.bot.get_context(interaction, cls=commands.Context)
    #     help_command = self.bot.help_command.copy()
    #     help_command.context = ctx
    #     if not needle:
    #         return [
    #             discord.app_commands.Choice(name=cog_name, value=cog_name)
    #             for cog_name, cog in self.bot.cogs.items()
    #             if await help_command.filter_commands(cog.get_commands())
    #         ][:25]
    #     needle = needle.lower()
    #     return [
    #         discord.app_commands.Choice(
    #             name=command.qualified_name, value=command.qualified_name
    #         )
    #         for command in await help_command.filter_commands(
    #             self.bot.walk_commands(), sort=True
    #         )
    #         if needle in command.qualified_name
    #     ][:25]


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Help(bot))
