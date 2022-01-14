import discord
import discord.utils
import numpy
import math
import os
from discord.ext import commands
from gears import style


class BotUtil:
    """
    Bot utility.
    """

    def __init__(self, bot) -> None:
        self.bot = bot

    async def len_file(self, file: str) -> int:
        """
        Return the file length for a given file

        Parameters
        ----------
        file: str
            The file to open and count

        Returns
        -------
        int
        """
        try:
            with open(file, encoding="utf8") as f:
                for i, l in enumerate(f):
                    pass
            return i + 1
        except Exception as e:
            print(e)
            return 0

    async def get_files(self, directory: str = None) -> list:
        """
        Return every file using recursion

        Parameters
        ----------
        directory: str (Optional)
            The directory to search, if none given opens then it leaves it

        Returns
        -------
        list
        """
        files = []
        if directory:
            if directory in ["__pycache__", "Databases"]:
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
            ):
                pass
            elif "." not in file:
                recursion = await self.get_files(f"{filepath}{file}")
                files = files + recursion
            else:
                files.append(f"{filepath}{file}")
        return files

    async def load_cogs(self, cogs) -> None:
        """
        Print and load a live feed,

        Parameters
        ----------
        cogs: list
            List of files that are in cogs in src/cogs

        Returns
        -------
        None
        """
        cog_list = []
        for file in cogs:
            try:
                if (
                    file.endswith(".py")
                    and not file.endswith("cog_template.py")
                    and not file.endswith("redis.py")
                    and not file.endswith("pastebin.py")
                ):
                    self.bot.load_extension(f"cogs.{file[:-3]}")
                    await self.bot.printer.print_cog_update(file[:-3], "LOAD")
                    cog_list.append(f"cogs.{file[:-3]}")

            except Exception as e:
                await self.bot.printer.print_cog_update(f"{file[:-3]}\n{e}", "FAIL")
        self.bot.cog_list = cog_list

    async def report_error(self, error_descrip):
        """
        Report an error by directly direct messaging me.

        Parameters
        ----------
        error_descrip: str
            Error description/message
        """

        ben = self.bot.get_user(360061101477724170)
        if not ben:
            ben = await self.bot.fetch_user(360061101477724170)

        embed = discord.Embed(
            title=f"Error Report",
            description=f"""""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("red"),
        )
        embed.set_thumbnail(url=style.get_emoji("image", "cancel"))
        await ben.send(embed=embed)


def default_cooldown_manager(msg):
    """
    Cooldown manager for commands

    def custom_cooldown(message):
        if message.author.permissions.manage_messages:
            return None  # no cooldown
        elif utils.get(message.author.roles, name="Nitro Booster"):
            return commands.Cooldown(2, 60)  # 2 per minute
        return commands.Cooldown(1, 60)  # 1 per minute

    @bot.command()
    @commands.dynamic_cooldown(custom_cooldown, commands.BucketType.user)
    async def ping(ctx):
        await ctx.send("pong")
    """
    user = ""  # global_db.find_one({"_id": msg.author.id})

    # Checking if the user is a patron and his/her level

    if user.get("PatronLevel") == 3:
        return commands.Cooldown(3.0, 5.0)
    elif user.get("PatronLevel") == 2:
        return commands.Cooldown(3.0, 6.0)

    # if msg.author.permissions.manage_messages:
    # return None
    # elif discord.utils.get(msg.author.roles, name="Nitro Booster"):
    # return commands.Cooldown(2, 60)  # 2 per minute
    # 3 Commands per 8 seconds if nothings been set
    return commands.Cooldown(3.0, 8.0)


def match_calc(string1, string2):
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
                distance[row - 1][col] + 1,  # Cost of deletions
                distance[row][col - 1] + 1,  # Cost of insertions
                distance[row - 1][col - 1] + cost,  # Cost of substitutions
            )
    ratio = ((len(string1) + len(string2)) - distance[row][col]) / (
        len(string1) + len(string2)
    )
    return int(ratio * 100)


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
    split = ""
    for i in text:
        if i in ["0", ":"]:
            split += i
        else:
            break
    return text.split(split)[1]


async def gen_loading_bar(self, percentage: float) -> list:
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
