import discord
from discord.ext import commands
from gears.style import c_get_color


class HelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        """When help is ran on its own no args"""
        embed = discord.Embed(
            title="Tenshi Help",
            color=c_get_color()
        )
        for cog, commands in mapping.items():
            command_signatures = [self.get_command_signature(c) for c in commands]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "ERROR")
                if cog_name in ["DevOnly", "ERROR", "Redis"]:
                    # Hiding certain names :L
                    pass
                else:
                    signatures = "\n".join(command_signatures)
                    embed.add_field(
                        name=cog_name, 
                        value=f"""```
{signatures}
```""", 
                        inline=True
                    )

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog):
        """Sending help for cogs"""
        embed = discord.Embed(
            title=cog.qualified_name,
            description=cog.description,
            color=c_get_color()
        )
        commands_view = ""
        for command in cog.get_commands():
            commands_view = f"{commands_view}\n{command}"

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
            color=c_get_color()
        )
        commands = ""
        for cc, command in enumerate(group.walk_commands(), start=1):
            commands = f"""{commands}\n{cc}. {str(command).replace(f"{group.name} ", "")}"""

        if commands == "":
            commands = "None"

        embed.add_field(
            name="Commands",
            value=f"""```md
{commands}
```""",
            inline=False
        )

        channel = self.get_destination()
        await channel.send(embed=embed)
    
    async def send_command_help(self, command):
        """Sending help for actual commands"""
        embed = discord.Embed(
            title=command.brief,
            description="",
            color=c_get_color()
        )
        #self.get_command_signature(command)
        embed.add_field(
            name="Help",
            value=command.help
        )
        alias = command.aliases
        if alias:
            alias_text = ", ".join(alias)
        else:
            alias_text = "None"
        
        alias_text = f"[Aliases]({alias_text})"

        embed.add_field(
            name="Usage",
            value=f"""```md
{self.get_command_signature(command)}
{alias_text}
```""",
            inline=False
        )

        embed.add_field(
            name="Extra Info",
            value=command.description,
            inline=False
        )
    
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_error_message(self, error):
        """Error Messages that may appear"""
        embed = discord.Embed(
            title="Error", 
            description=error,
            color=c_get_color("red")
        )
        channel = self.get_destination()
        await channel.send(embed=embed)


class Help(commands.Cog):
    """The help cog"""
    def __init__(self, bot):
       self.bot = bot

       help_command = HelpCommand()
       help_command.cog = self
       bot.help_command = help_command


def setup(bot):
    bot.add_cog(Help(bot))
