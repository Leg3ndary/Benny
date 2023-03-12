import datetime

from colorama import Fore, Style
from discord.ext import commands


class TerminalPrinter:
    """
    Print info and updates to terminal quickly and nicely
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init for the printer
        """
        self.bot: commands.Bot = bot

    def print_header(self) -> None:
        """
        Print the header
        """
        print(
            Fore.CYAN
            + r"""
|================================================|
| _____                        _____       __    |
| | __ )  ___ _ __  _ __  _   _| __ )  ___ | |_  |
| |  _ \ / _ \ '_ \| '_ \| | | |  _ \ / _ \| __| |
| | |_) |  __/ | | | | | | |_| | |_) | (_) | |_  |
| |____/ \___|_| |_|_| |_|\__, |____/ \___/ \__| |
|                         |___/                  |
|================================================|"""
        )

    def gen_category(self, category: str) -> str:
        """
        Generate a category and return so this looks cool

        Parameters
        ----------
        category: str
            What the middle text should be

        Returns
        -------
        str
        """
        time_str = datetime.datetime.now().strftime("%x | %X")
        categorystr = f"[{Style.RESET_ALL} {category} {Fore.WHITE}]{Style.RESET_ALL}"
        generated = (
            f"""{Fore.WHITE}[{Style.RESET_ALL} {time_str} {Fore.WHITE}]{categorystr}"""
        )
        return generated

    async def load(self, info: str) -> None:
        """
        [LOAD] When something has loaded.

        Parameters
        ----------
        info: str
            The info you want to print out after
        """
        msg = f"{self.gen_category(f'{Fore.BLUE}LOADED')} {info}"
        print(msg)

    async def cog_update(self, cog: str, update: str) -> None:
        """
        [COG LOAD|UNLOAD|RELOAD] When a cog is loaded or unloaded (ALSO ON SYNC)

        Parameters
        ----------
        cog: str
            The cog that's been updated
        update:
            The update kind, LOAD|UNLOAD|RELOAD
        """
        if update == "LOAD":
            category = f"{Fore.GREEN}COG LOAD"
        elif update == "UNLOAD":
            category = f"{Fore.RED}COG UNLOAD"
        elif update == "RELOAD":
            category = f"{Fore.MAGENTA}COG RELOAD"
        elif update == "FAIL":
            category = f"{Fore.RED}COG FAILED"
        msg = f"{self.gen_category(category)} {cog}"
        print(msg)

    async def bot_update(self, status: str) -> None:
        """
        [LOGGED IN|LOGGED OUT] When the bots logged in or logged out with relevant info

        Parameters
        ----------
        status: str
            The status to print in the category
        """
        discrim = f"{self.bot.user.name}#{self.bot.user.discriminator}"
        msg = f"{self.gen_category(f'{Fore.CYAN}{status}')} {discrim}"
        print(msg)

    async def connect(self, info: str) -> None:
        """
        [CONNECTED] When the bot has connected successfully to something

        Parameters
        ----------
        info: str
            The info to add and print
        """
        msg = f"{self.gen_category(f'{Fore.YELLOW}CONNECTED')} {info}"
        print(msg)

    async def bot_info(self, categories: str, info: str):
        """
        [BOT] Bot related info that needs to be printed

        Parameters
        ----------
        categories: str
            Extra categories if I need it
        info: str
            The info to add or print
        """
        msg = f"{self.gen_category(f'{Fore.CYAN}BOT')}{categories} {info}"
        print(msg)

    async def cog(self, categories: str, info: str):
        """
        [COG] Cog related info that needs to be printed

        Parameters
        ----------
        categories: str
            Extra categories if I need it
        info: str
            The info to add or print
        """
        msg = f"{self.gen_category(f'{Fore.RED}COG')}{categories} {info}"
        print(msg)
