from colorama import Style, Fore, Back

"""
Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Style: DIM, NORMAL, BRIGHT, RESET_ALL
"""



class InfoPrinter:
    """Printing info to our terminal from our bot in a nice way"""
    def __init__(self) -> None:
        pass

    async def print_load(self, info: str) -> None:
        """Print out something loaded"""
        print(f"[{Style.BRIGHT}{Fore.BLUE}LOADED{Style.RESET_ALL}] {info}")

    async def print_cog_update(self, cog: str, update: str):
        """Print out when a cog is loaded or unloaded"""
        if update == "LOAD":
            category = f"{Fore.GREEN}COG LOAD"
        elif update == "UNLOAD":
            category = f"{Fore.RED}COG UNLOAD"
        elif update == "RELOAD":
            category = f"{Fore.MAGENTA}COG RELOAD"
        print(f"[{category}{Style.RESET_ALL}] {cog}")