import datetime
import math
import os
import time
from typing import Tuple

import aiohttp
import discord
from colorama import Fore, Style
from discord.ext import commands


class BotUtil:
    """
    Bot utility.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init the bot
        """
        self.bot = bot

    async def len_file(self, file: str) -> Tuple[int, int]:
        """
        Return the file length for a given file
        Parameters
        ----------
        file: str
            The file to open and count
        Returns
        -------
        Tuple[int, int]
        """
        if file not in [".github", ".vscode"]:
            with open(file, encoding="utf8") as _file:
                lines = len(_file.readlines())
            with open(file, encoding="utf8") as _file:
                chars = len(_file.read())
            return (lines, chars)
        else:
            return (0, 0)

    async def get_files(self, directory: str = None) -> list:
        """
        Return every file using recursion

        Parameters
        ----------
        directory: str (Optional None)
            The directory to search, if none given opens then it leaves it

        Returns
        -------
        list
        """
        files = []
        if directory:
            if directory in [
                "__pycache__",
                "Databases",
                "Logs",
                ".vscode",
                "Docs",
                "Website",
            ]:
                directories = []
            else:
                directories = os.listdir(directory)
                filepath = directory + "/"
        else:
            filepath = ""
            directories = os.listdir()

        for file in directories:
            if (
                file.endswith(".exe")
                or file.endswith(".png")
                or file.endswith(".pyc")
                or file.endswith(".jar")
                or file.endswith(".git")
                or file.endswith(".pytest_cache")
            ):
                pass
            elif "." not in file:
                recursion = await self.get_files(f"{filepath}{file}")
                files = files + recursion
            else:
                files.append(f"{filepath}{file}")
        return files

    async def load_cogs(self, cogs: list) -> None:
        """
        Print and load a live feed

        Parameters
        ----------
        cogs: list
            List of files that are in cogs in src/cogs

        Returns
        -------
        None
        """
        cog_list = []
        if self.bot.config.get("Cogs"):
            cogs = self.bot.config.get("Cogs")
            for file in cogs:
                try:
                    await self.bot.load_extension(f"cogs.{file[:-3]}")
                    await self.bot.blogger.cog_update(file[:-3], "LOAD")
                    cog_list.append(f"cogs.{file[:-3]}")

                except Exception as e:
                    await self.bot.blogger.cog_update(f"{file[:-3]}\n{e}", "FAIL")
                    print(e.with_traceback)

        else:
            for file in cogs:
                try:
                    filename = file.split("/")[-1][:-3]
                    if file.endswith(".py") and (filename not in ["cog_template"]):
                        await self.bot.load_extension(f"cogs.{file[:-3]}")
                        await self.bot.blogger.cog_update(file[:-3], "LOAD")
                        cog_list.append(f"cogs.{file[:-3]}")

                except Exception as e:
                    await self.bot.blogger.cog_update(f"{file[:-3]}\n{e}", "FAIL")
                    print(e.with_traceback)

        self.bot.cog_list = cog_list


# hidden func
'''
def match_calc(string1: str, string2: str) -> int:
    """Calculate how much 2 different strings match each other"""
    rows = len(string1) + 1
    cols = len(string2) + 1
    distance = numpy.zeros((rows, cols), dtype=int)

    for i in range(1, rows):
        for k in range(1, cols):
            distance[i][0] = i
            distance[0][k] = k

    for col in range(1, cols):
        for row in range(1, rows):
            if string1[row - 1] == string2[col - 1]:
                cost = 0
            else:
                cost = 2
            distance[row][col] = min(
                distance[row - 1][col] + 1,         # Cost of deletions
                distance[row][col - 1] + 1,         # Cost of insertions
                distance[row - 1][col - 1] + cost,  # Cost of substitutions
            )
    ratio = ((len(string1) + len(string2)) - distance[row][col]) / (
        len(string1) + len(string2)
    )
    return int(ratio * 100)
'''


def remove_zcs(text: str) -> str:
    """
    Remove leading zeros and colons

    Parameters
    ----------
    text: str
        The text to remove colons and zeros from

    Returns
    -------
    str
    """
    text = text.split(".")[0]
    split = ""
    for i in text:
        if i in ["0", ":"]:
            split += i
        else:
            break
    if split == "":
        return text
    return text.split(split)[1]


async def gen_loading_bar(percentage: float) -> list:
    """
    Generate a nice loading bar based on the stuff we output, returns in a list format
    An embed can have up to ████████████████████████████████████████████████████████████ (60 things)
    """
    bar_num = math.trunc(percentage / (100 / 60))

    bars = []
    bars.append(bar_num * "█")
    bars.append((60 - bar_num) * "█")


ANSI_COLOR_DICT = {
    "RESET": "0",
    "CLEAR": "0",
    "NORMAL": "0",
    "GREY": "30",
    "GRAY": "30",
    "RED": "31",
    "GREEN": "32",
    "YELLOW": "33",
    "BLUE": "34",
    "PINK": "35",
    "CYAN": "36",
    "WHITE": "37",
}

BACKGROUND_DICT = {
    "DARK": "40",
    "DARKBLUE": "40",
    "ORANGE": "41",
    "GREY4": "42",
    "GRAY4": "42",
    "GREY3": "43",
    "GRAY3": "43",
    "GREY2": "44",
    "GRAY2": "44",
    "INDIGO": "45",
    "GREY1": "46",
    "GRAY1": "46",
    "WHITE": "47",
}

STYLE_DICT = {"RESET": "0", "CLEAR": "0", "BOLD": "1", "UNDERLINE": "4"}


def ansi(color, background=None, style=None, style2=None) -> str:
    """Generates codes for you in a nice way"""
    origin = "["
    if style:
        origin += STYLE_DICT.get(style.upper()) + ";"
    if background:
        origin += BACKGROUND_DICT.get(background.upper()) + ";"
    if style2:
        origin += STYLE_DICT.get(style2.upper()) + ";"
    if origin == "[":
        origin += "0;"

    origin += ANSI_COLOR_DICT.get(color.upper()) + "m"
    return origin


class BotLogger:
    """
    Printing info to our terminal from our bot in a nice way
    """

    def __init__(self, bot: commands.Bot, session: aiohttp.ClientSession) -> None:
        """
        Init for the printer
        """
        self.bot = bot
        self.webhook_url = bot.config.get("Bot").get("Webhook")
        self.last_sent = int(time.time()) - 13
        self.updates = []
        self.session = session
        self.webhook = discord.Webhook.from_url(url=self.webhook_url, session=session)

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
