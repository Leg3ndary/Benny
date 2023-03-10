import math
import os
from enum import Enum
from typing import Tuple

from discord.ext import commands


class BotUtil:
    """
    Bot utility class which has small functions that I may need to use
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
        if file not in (".github", ".vscode"):
            with open(file, encoding="utf8") as _file:
                lines = len(_file.readlines())
            with open(file, encoding="utf8") as _file:
                chars = len(_file.read())
            return (lines, chars)
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
            if directory in (
                "__pycache__",
                "databases",
                "logs",
                ".vscode",
                "assets",
                "plugins",
            ):
                directories = []
            else:
                directories = os.listdir(directory)
                filepath = directory + "/"
        else:
            filepath = ""
            directories = os.listdir()

        for file in directories:
            if True in map(
                file.endswith,
                (
                    ".exe",
                    ".png",
                    ".pyc",
                    ".git",
                    ".gitignore",
                    ".jar",
                    "pytest_cache",
                    ".vscode",
                    ".github",
                    ".pdf",
                ),
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
                    await self.bot.terminal.cog_update(file[:-3], "LOAD")
                    cog_list.append(f"cogs.{file[:-3]}")

                except Exception as e:
                    await self.bot.terminal.cog_update(f"{file[:-3]}\n{e}", "FAIL")
                    print(e.with_traceback)

        else:
            for file in cogs:
                try:
                    filename = file.split("/")[-1][:-3]
                    if file.endswith(".py") and (
                        filename not in ("cog_template", "mod", "levels")
                    ):
                        await self.bot.load_extension(f"cogs.{file[:-3]}")
                        await self.bot.terminal.cog_update(file[:-3], "LOAD")
                        cog_list.append(f"cogs.{file[:-3]}")

                except Exception as e:
                    await self.bot.terminal.cog_update(f"{file[:-3]}\n{e}", "FAIL")
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


class AnsiColor(Enum):
    """
    Ansi color codes
    """

    RESET = "0"
    CLEAR = "0"
    NORMAL = "0"
    GREY = "30"
    GRAY = "30"
    RED = "31"
    GREEN = "32"
    YELLOW = "33"
    BLUE = "34"
    PINK = "35"
    CYAN = "36"
    WHITE = "37"


class AnsiBackground(Enum):
    """
    Ansi background color codes
    """

    DARK = "40"
    DARKBLUE = "40"
    ORANGE = "41"
    GREY4 = "42"
    GRAY4 = "42"
    GREY3 = "43"
    GRAY3 = "43"
    GREY2 = "44"
    GRAY2 = "44"
    INDIGO = "45"
    GREY1 = "46"
    GRAY1 = "46"
    WHITE = "47"


class AnsiStyle(Enum):
    """
    Ansi style color codes
    """

    RESET = "0"
    CLEAR = "0"
    BOLD = "1"
    UNDERLINE = "4"


def ansi(
    color: str, background: str = None, style: str = None, style2: str = None
) -> str:
    """
    Generates codes for you in a nice way
    """
    origin = "["
    if style:
        origin += AnsiStyle[style.upper()].value + ";"
    if background:
        origin += AnsiBackground[background.upper()].value + ";"
    if style2:
        origin += AnsiStyle[style.upper()].value + ";"
    if origin == "[":
        origin += "0;"
    origin += AnsiColor[color.upper()].value + "m"
    return origin
