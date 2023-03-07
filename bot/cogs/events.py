import logging
import math

import discord
import discord.utils
from colorama import Fore
from discord.ext import commands, tasks
from gears import style


class SelectPage(discord.ui.Modal, title="Type a Page"):
    """
    Select a page number to view.
    """

    page = discord.ui.TextInput(
        label="Page", placeholder="1", max_length=5, required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Thanks for your response, {self.name}!", ephemeral=True
        )


class LoggerPaginator(discord.ui.View):
    """
    Logger Paginator
    """

    def __init__(self) -> None:
        """
        Construct the paginator
        """
        super().__init__()
        lines = (x for x in open("logs/benny.log", "r", encoding="utf8").readlines())
        pages = []
        ctotal = 10
        current = []
        for line in lines:
            if ctotal < 2000:
                current.append(line)
                ctotal += len(line) + 2
            else:
                pages.append("\n".join(current))
                ctotal = 6
                current = []

        self.pages = tuple(pages)
        if not self.pages:
            self.pages = ("No logs found.",)
        self.current_page = 0

    async def generate_page(self, interaction: discord.Interaction) -> None:
        """
        Generate the new page based on current page
        """
        embed = discord.Embed(
            title="Benny Logs",
            description=f"""```
{self.pages[self.current_page]}
            ```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.BLACK,
        )
        embed.set_footer(
            text=f"Page {self.current_page + 1}/{len(self.pages)}",
        )
        await interaction.edit_original_message(embed=embed)

    def change_page(self, page: int) -> None:
        """
        Change the current page
        """
        self.current_page = page
        if self.current_page < 0:
            self.current_page = 0
        elif self.current_page > len(self.pages):
            self.current_page = len(self.pages) - 1

    @discord.ui.button(
        emoji=style.Emoji.REGULAR.left, style=discord.ButtonStyle.blurple
    )
    async def on_backward(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """
        Go to next page
        """
        self.change_page(-1)
        await self.generate_page(interaction)

    @discord.ui.button(emoji=style.Emoji.REGULAR.stop, style=discord.ButtonStyle.red)
    async def on_stop(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        for child in self.children:
            child.disabled = True
        self.stop()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(
        emoji=style.Emoji.REGULAR.right, style=discord.ButtonStyle.blurple
    )
    async def on_forward(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """
        Go to next page
        """
        self.change_page(1)
        await self.generate_page(interaction)

    @discord.ui.button(emoji=style.Emoji.REGULAR.search, style=discord.ButtonStyle.grey)
    async def on_search(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """
        Search a page
        """
        self.current_page = 0
        self.change_page(0)
        await self.generate_page(interaction)

    async def start(self, ctx: commands.Context) -> None:
        """
        Start the paginator
        """
        self.current_page = 0
        embed = discord.Embed(
            title="Benny Logs",
            description=f"""```
{self.pages[self.current_page]}
            ```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.BLACK,
        )
        embed.set_footer(
            text=f"Page {self.current_page + 1}/{len(self.pages)}",
        )
        await ctx.send(embed=embed, view=self)


class Events(commands.Cog):
    """
    Events that I wanna receive but don't really have a cog for
    """

    COLOR = style.Color.BLUE
    ICON = "🕖"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init for events
        """
        self.bot = bot
        self.logger = logging.getLogger("Benny")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(
            filename="logs/benny.log", encoding="utf-8", mode="w"
        )
        handler.setFormatter(
            logging.Formatter(
                "[ %(asctime)s ] [ %(levelname)s ] [ %(name)s.events ] %(message)s"
            )
        )
        self.logger.addHandler(handler)
        self.ping_loop.start()

    async def cog_unload(self) -> None:
        """
        Unload the the pingloop
        """
        self.ping_loop.cancel()

    @tasks.loop(seconds=15.0)
    async def ping_loop(self) -> None:
        """
        Update bot latency dict every 3 seconds
        """
        if len(self.bot.ping_list) > 10:
            self.bot.ping_list.pop(0)
        self.bot.ping_list.append(self.bot.latency)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """
        When we join a guild print it out
        """
        if guild.get_member(360061101477724170) or (
            await guild.fetch_member(360061101477724170)
        ):
            return

        guild_bots = 0
        for member in guild.members:
            if member.bot:
                guild_bots += 1

        humans = len(guild.members) - guild_bots

        bot_percentage = math.trunc((guild_bots / len(guild.members)) * 10000) / 100

        await self.bot.blogger.bot_info(
            self.bot.blogger.gen_category(f"{Fore.GREEN}JOINED"),
            f" {guild.name} {guild.id} | Server is {bot_percentage}% Bots ({guild_bots}/{len(guild.members)})",
        )
        self.logger.info(f"Joined Guild {guild.name} ({guild.id})")

        if bot_percentage > 20 and humans < 5:
            sent = False
            embed = discord.Embed(
                title="Sorry!",
                description=f"""Your server has **{guild_bots} Bots ** compared to **{len(guild.members)} Members**
                Either:
                - Have `6+` humans (Currently **{humans}** humans)
                - Lower your servers percentage of bots to under 20% (Currently **{bot_percentage}%** bots)""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            for channel in guild.channels:
                if "general" in channel.name:
                    await channel.send(embed=embed)
                    sent = True
                    break
            if not sent:
                try:
                    await guild.channels[0].send(embed=embed)
                except:
                    pass
            await guild.leave()
            await self.bot.blogger.bot_info(
                self.bot.blogger.gen_category(f"{Fore.MAGENTA}AUTOLEFT"),
                f" {guild.name} {guild.id}",
            )
            self.logger.info(f"AutoLeft Guild {guild.name} ({guild.id})")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """
        When we leave a guild
        """
        await self.bot.blogger.bot_info(
            self.bot.blogger.gen_category(f"{Fore.RED}LEFT"),
            f" {guild.name} {guild.id}",
        )
        self.logger.info(f"Left Guild {guild.name} ({guild.id})")

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread) -> None:
        """
        Whenever possible, join threads
        """
        await thread.join()

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context) -> None:
        """
        On a command used track it
        """
        self.logger.info(
            f"Command {ctx.command.name} used by {ctx.author.name} ({ctx.author.id}) in {ctx.guild.name} ({ctx.guild.id})"
        )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        """
        On interaction, log it
        """
        _type = interaction.type
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
        self.logger.info(
            f"Interaction type {interstr} used by {interaction.user.name} ({interaction.user.id}) in {interaction.guild.name} ({interaction.guild.id})"
        )

    @commands.command(
        name="blogs",
        description="""Description of command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.is_owner()
    async def blogs_cmd(self, ctx: commands.Context, page: int) -> None:
        """
        View logs
        """
        paginator = LoggerPaginator()
        await paginator.start(ctx)

    @commands.Cog.listener()
    async def on_log_info(self, msg: str) -> None:
        """
        Log info
        """
        self.logger.info(msg)

    @commands.Cog.listener()
    async def on_log_debug(self, msg: str) -> None:
        """
        Log debug
        """
        self.logger.debug(msg)

    @commands.Cog.listener()
    async def on_log_warn(self, msg: str) -> None:
        """
        Log warning
        """
        self.logger.warning(msg)

    @commands.Cog.listener()
    async def on_log_error(self, msg: str) -> None:
        """
        Log error
        """
        self.logger.error(msg)

    @commands.Cog.listener()
    async def on_log_critical(self, msg: str) -> None:
        """
        Log critical
        """
        self.logger.critical(msg)


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Events(bot))
