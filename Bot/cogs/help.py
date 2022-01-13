import discord
from discord.commands import SlashCommand
from discord.ext import commands
from gears import style


class BennyHelp(commands.HelpCommand):
    """Custom Help Command Class"""

    def get_command_signature(self, command):
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

        alias = command.name if not parent_sig else parent_sig + " " + command.name

        return f"{self.context.clean_prefix}{alias} {command.signature}"

    async def send_bot_help(self, mapping):
        """When help is ran on its own no args"""
        embed = discord.Embed(
            title="Help",
            color=style.get_color()
        )
        for cog, commands in mapping.items():
            command_signatures = []

            for command in commands:
                if isinstance(command, SlashCommand):
                    pass
                else:
                    command_signatures.append(self.get_command_signature(command))

            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "ERROR")
                if cog_name in ["ERROR", "Dev", "CustomCommands"]:
                    pass
                else:
                    signatures = "\n".join(command_signatures)
                    embed.add_field(
                        name=cog_name,
                        value=f"""```
{signatures}
```""",
                        inline=True,
                    )

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog):
        """Sending help for cogs"""
        embed = discord.Embed(
            title=cog.qualified_name,
            description=cog.description,
            color=style.get_color(),
        )
        commands_view = "\n".join(cog.get_commands())
        embed.add_field(
            name="Commands",
            value=commands_view,
            inline=False
        )
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_group_help(self, group):
        """Sending help for groups"""
        embed = discord.Embed(
            title=group.name,
            description=f"""{group.short_doc}""",
            color=style.get_color(),
        )
        for command in group.walk_commands():
            embed.add_field(
                name=self.get_command_signature(command),
                value=command.brief,
                inline=False
            )
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command):
        """
        Sending help for actual commands
        """
        embed = discord.Embed(
            title=self.get_command_signature(command),
            description=command.description,
            color=style.get_color(),
        )
        embed.add_field(
            name="Help",
            value=command.help
        )
        alias = command.aliases
        if alias:
            alias_text = ", ".join(alias)
        else:
            alias_text = "<No Aliases>"
        embed.add_field(
            name="Usage and Aliases",
            value=f"""```md
{self.get_command_signature(command)}

{alias_text}
```""",
            inline=False,
        )
        embed.set_author(
            name=f"{self.context.author.name}#{self.context.author.discriminator}",
            url=self.context.author.avatar,
        )

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_error_message(self, error):
        """Error Messages that may appear"""
        embed = discord.Embed(
            title="Error", description=error, color=style.get_color("red")
        )
        channel = self.get_destination()
        await channel.send(embed=embed)


class Help(commands.Cog):
    """The help cog"""

    def __init__(self, bot):
        self.bot = bot
        help_command = BennyHelp()
        help_command.cog = self
        bot.help_command = help_command


def setup(bot):
    bot.add_cog(Help(bot))
