from colorama import Back, Fore, Style


"""
Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Style: DIM, NORMAL, BRIGHT, RESET_ALL
"""


class InfoPrinter:
    """Printing info to our terminal from our bot in a nice way"""

    def __init__(self, bot) -> None:
        self.bot = bot

    async def generate_category(self, category: str) -> str:
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
        brackets = (
            f"{Fore.WHITE}[{Style.RESET_ALL} {category} {Fore.WHITE}]{Style.RESET_ALL}"
        )
        return brackets

    async def p_load(self, info: str):
        """
        [LOAD] When something has loaded.

        Parameters
        ----------
        info: str
            The info you want to print out after
        """
        print(f"{await self.generate_category(f'{Fore.BLUE}LOADED')} {info}")

    async def p_cog_update(self, cog: str, update: str):
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
            category = f"{Fore.RED}COG FAIL"
        print(f"{await self.generate_category(category)} {cog}")

    async def p_bot_update(self, status: str):
        """
        [LOGGED IN|LOGGED OUT] When the bots logged in or logged out with relevant info

        Parameters
        ----------
        status: str
            The status to print in the category
        """
        print(
            f"{await self.generate_category(f'{Fore.CYAN}{status}')} {self.bot.user.name}#{self.bot.user.discriminator}"
        )

    async def p_connect(self, info: str) -> None:
        """
        [CONNECTED] When the bot has connected successfully to something

        Parameters
        ----------
        info: str
            The info to add and print
        """
        print(f"{await self.generate_category(f'{Fore.YELLOW}CONNECTED')} {info}")

    async def p_bot(self, categories: str, info: str):
        """
        [BOT] Bot related info that needs to be printed

        Parameters
        ----------
        categories: str
            Extra categories if I need it
        info: str
            The info to add or print
        """
        print(f"{await self.generate_category(f'{Fore.CYAN}BOT')}{categories} {info}")

    async def p_update_db(self, dbtype: str, name: str, info: str):
        """
        [DB] DB related info that needs to be printed

        Parameters
        ----------
        dbtype
        info: str
            The info to add or print
        """
        print(f"{await self.generate_category(f'{Fore.MAGENTA}DB')} {info}")

    async def p_cog(self, categories: str, info: str):
        """
        [COG] Cog related info that needs to be printed

        Parameters
        ----------
        categories: str
            Extra categories if I need it
        info: str
            The info to add or print
        """
        print(f"{await self.generate_category(f'{Fore.RED}COG')}{categories} {info}")

    async def p_save(self, info: str):
        """
        [SAVE] Save info

        Parameters
        ----------
        info: str
            The info to add or print
        """
        print(f"{await self.generate_category(f'{Fore.GREEN}SAVE')} {info}")
