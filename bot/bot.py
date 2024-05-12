"""
Main Benny Bot File

Please read the license.
"""

import asyncio
import datetime
import json
import logging
import os
import sys
import time
from copy import copy
from typing import List

import aiohttp
import asqlite
import discord
import mystbin
from api import BotApp
from cogs.tags import Tags
from discord.ext import commands
from gears import cooldowns, users, util
from gears.database import BennyDatabases
from gears.terminal_printer import TerminalPrinter

start = time.monotonic()

with open("bot_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="logs/discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
)
logger.addHandler(handler)

intents = discord.Intents(
    bans=True,
    dm_messages=True,
    dm_reactions=True,
    dm_typing=False,
    emojis=True,
    guild_messages=True,
    guild_reactions=True,
    guild_typing=False,
    guilds=True,
    integrations=False,
    invites=True,
    members=True,
    messages=True,
    presences=False,
    reactions=False,
    typing=False,
    voice_states=True,
    webhooks=True,
    message_content=True,
)


async def get_prefix(_bot: commands.Bot, msg: discord.Message) -> List[str]:
    """
    Gets the prefix from built cache, if a guild isn't found (Direct Messages) assumes
    prefix is just pinging the bot

    Raises AttributeError when the cache isn't built so we just have this quick fix,
    the bot itself won't respond to anything until prefixes are built but this
    silences noisy errors.
    """
    prefixes = [f"<@!{_bot.user.id}> ", f"<@{_bot.user.id}> "]
    if _bot.LOADED_PREFIXES:
        if msg.guild:
            return prefixes + _bot.prefixes.get(str(msg.guild.id), "")
        return prefixes.append(_bot.prefix)
    return ""


async def when_bot_ready() -> None:
    """
    On ready dispatch and print stuff
    """
    await bot.wait_until_ready()
    dispatches = (
        "load_prefixes",
        "initiate_all_tags",
        "connect_wavelink",
        "load_sentinel_managers",
        "load_reminders",
        "load_users",
    )
    for dispatch in dispatches:
        bot.dispatch(dispatch)
    await bot.terminal.bot_update("LOGGED IN")


class BennyBot(commands.Bot):
    """
    Custom class for Benny!
    """

    PLATFORM = sys.platform.lower()
    START_TIME: float = datetime.datetime.now(datetime.timezone.utc)
    LOADED_PREFIXES: bool = False
    MUSIC_ENABLED: bool = True
    PREFIX: str = config.get("Bot").get("Prefix")
    sessions: dict = {
        "main": None,
        "base": None,
        "music": None,
        "sentinel": None,
        "discordstatus": None,
    }
    terminal: TerminalPrinter = None
    config: dict = config
    file_list: dict = {}
    app: BotApp = None
    ping_list: list = []
    databases: BennyDatabases = BennyDatabases()
    user_manager: users.UserManager = None
    wavelink = None

    def __init__(self) -> None:
        """
        Init for the bot
        """
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            description="Benny Bot",
        )
        self.util: util.BotUtil = None
        self.pcc: cooldowns.PremiumChecker = None
        self.tag_cog: Tags = None
        self.mystbin: mystbin.Client = mystbin.Client()

    async def async_init(self) -> None:
        """
        Setup hook for the bot

        1. Super setup hook
        2. Connect and set both databases
        3. Create all aiohttp user sessions
        4. Create and set the bot logger
        5. Create and set bot util
        """

        await super().setup_hook()

        self.databases.users = await asqlite.connect("databases/users.db")
        self.databases.servers = await asqlite.connect("databases/servers.db")

        await self.create_sessions()

        self.util = util.BotUtil(bot)
        await bot.terminal.load("Bot Util")

        lines = 0
        chars = 0
        for file in await self.util.get_files():
            file_len = await self.util.len_file(file)
            self.file_list[file] = f"{file_len[0]} lines, {file_len[1]} chars"
            lines += file_len[0]
            chars += file_len[1]
        self.file_list["total"] = f"{lines} lines, {chars} chars"

        self.pcc = cooldowns.PremiumChecker(bot)
        self.pcc.premium_list = []

    async def create_sessions(self) -> None:
        """
        Create a session for every key in sessions dict
        """
        for k in self.sessions:
            self.sessions[k] = aiohttp.ClientSession(loop=self.loop)

    async def close(self) -> None:
        """
        Close all aiohttp sessions on close as well as databases
        """
        await super().close()
        for session in self.sessions.values():
            await session.close()
        await self.databases.users.close()
        await self.databases.servers.close()

    async def on_message(self, message: discord.Message) -> None:
        """
        On message run through a few steps

        1. Ignore all bots, I don't care
        2. Process any and all commands
        3. Check if the command is a tag and we need to invoke it (Redo this ugly shit)
        """
        if message.author.bot:
            return

        await self.process_commands(message)

        # Tags
        ctx = await self.get_context(message)

        if (
            ctx.invoked_with
            and ctx.invoked_with.lower() not in self.commands
            and ctx.command is None
        ):
            msg = copy(message)
            if ctx.prefix and ctx.guild:
                args = msg.content[len(ctx.prefix) :].split(" ", 1)
                if len(args) > 1:
                    args = args[-1]
                else:
                    args = ""
                named_tags = self.tag_cog.custom_tags.get(ctx.invoked_with)
                if named_tags:
                    _tag = named_tags.get(str(ctx.guild.id))
                    if _tag:
                        await self.tag_cog.invoke_custom_command(ctx, args, _tag, True)


bot = BennyBot()


@bot.check
async def global_check(ctx: commands.context) -> bool:
    """
    Global check that applies to all commands
    ├─ Check if prefixes are actually loaded
    ├── Check if it's me, if so, let me do anything L
    ├─── Check if the user is blacklisted from the bot
    ├──── Check if command is disabled
    ├───── Check if channel/thread is being ignored
    └───────
    """
    if not bot.LOADED_PREFIXES:
        return False
    if ctx.author.id == bot.owner_id:
        return True
    return True


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: discord.app_commands.AppCommandError
) -> None:
    """
    Error handler for app commands
    """
    bot.dispatch("send_app_command_error", interaction, error)


async def start_bot() -> None:
    """
    Start the bot with everything it needs
    """
    async with bot:
        bot.terminal = TerminalPrinter(bot)
        bot.terminal.print_header()
        await bot.terminal.load("Terminal Printer")

        await bot.async_init()

        await bot.util.load_cogs(os.listdir("bot/cogs"))
        bot.tag_cog = bot.get_cog("Tags")

        end = time.monotonic()
        total_load = (round((end - start) * 1000, 2)) / 1000

        await bot.terminal.bot_info(
            "",
            f"Bot loaded in approximately {total_load} seconds",
        )

        bot.loop.create_task(when_bot_ready())

        # bot.app = BotApp(bot)
        # await bot.app.start("0.0.0.0", 8080)
        # await bot.terminal.bot_info("", "Started Webserver")

        await bot.start(
            bot.config.get("Bot").get("Token")
            if bot.config.get("Bot").get("Dev_Token") is None
            else bot.config.get("Bot").get("Dev_Token")
        )


# if bot.PLATFORM == "linux":
#     uvloop.install()

asyncio.run(start_bot())
