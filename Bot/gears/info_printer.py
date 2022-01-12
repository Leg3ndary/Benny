from colorama import Style, Fore, Back

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
        """Generate a category so this looks cool"""
        brackets = f"{Fore.WHITE}[{Style.RESET_ALL} {category} {Fore.WHITE}]{Style.RESET_ALL}"
        return brackets

    async def print_load(self, info: str) -> None:
        """Print out something loaded"""
        print(f"{await self.generate_category(f'{Fore.BLUE}LOADED')} {info}")

    async def print_cog_update(self, cog: str, update: str) -> None:
        """Print out when a cog is loaded or unloaded"""
        if update == "LOAD":
            category = f"{Fore.GREEN}COG LOAD"
        elif update == "UNLOAD":
            category = f"{Fore.RED}COG UNLOAD"
        elif update == "RELOAD":
            category = f"{Fore.MAGENTA}COG RELOAD"
        print(f"{await self.generate_category(category)} {cog}")

    async def print_bot_update(self, status: str) -> None:
        """Print when the bots logged in with relevant info"""
        print(f"{await self.generate_category(f'{Fore.CYAN}{status}')} {self.bot.user.name}#{self.bot.user.discriminator}")
    
    async def print_connect(self, info: str) -> None:
        """Print that we have connected to something"""
        print(f"{await self.generate_category(f'{Fore.YELLOW}CONNECTED')} {info}")