import discord
from discord.ext import commands, menus


class MyMenuPages(ui.View, menus.MenuPages):
    def __init__(self, source, *, delete_message_after=False):
        super().__init__(timeout=60)
        self._source = source
        self.current_page = 0
        self.ctx = None
        self.message = None
        self.delete_message_after = delete_message_after

    async def start(self, ctx, *, channel=None, wait=False):
        # We wont be using wait/channel, you can implement them yourself. This is to match the MenuPages signature.
        await self._source._prepare_once()
        self.ctx = ctx
        self.message = await self.send_initial_message(ctx, ctx.channel)

    async def _get_kwargs_from_page(self, page):
        """This method calls ListPageSource.format_page class"""
        value = await super()._get_kwargs_from_page(page)
        if "view" not in value:
            value.update({"view": self})
        return value

    async def interaction_check(self, interaction):
        """Only allow the author that invoke the command to be able to use the interaction"""
        return interaction.user == self.ctx.author

    @ui.button(
        emoji="<:before_fast_check:754948796139569224>",
        style=discord.ButtonStyle.blurple,
    )
    async def first_page(self, button, interaction):
        await self.show_page(0)

    @discord.ui.button(
        emoji="<:before_check:754948796487565332>", style=discord.ButtonStyle.blurple
    )
    async def before_page(self, button, interaction):
        await self.show_checked_page(self.current_page - 1)

    @discord.ui.button(
        emoji="<:stop_check:754948796365930517>", style=discord.ButtonStyle.blurple
    )
    async def stop_page(self, button, interaction):
        self.stop()
        if self.delete_message_after:
            await self.message.delete(delay=0)

    @discord.ui.button(
        emoji="<:next_check:754948796361736213>", style=discord.ButtonStyle.blurple
    )
    async def next_page(self, button, interaction):
        await self.show_checked_page(self.current_page + 1)

    @discord.ui.button(
        emoji="<:next_fast_check:754948796391227442>", style=discord.ButtonStyle.blurple
    )
    async def last_page(self, button, interaction):
        await self.show_page(self._source.get_max_pages() - 1)


class MyHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        return "%s%s %s" % (
            self.clean_prefix,
            command.qualified_name,
            command.signature,
        )

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Help")
        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = [self.get_command_signature(c) for c in filtered]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                embed.add_field(
                    name=cog_name, value="\n".join(command_signatures), inline=False
                )

        channel = self.get_destination()
        await channel.send(embed=embed)


class YourCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        help_command = MyHelp()
        help_command.cog = self
        bot.help_command = help_command


def setup(bot):
    bot.add_cog(YourCog(bot))
