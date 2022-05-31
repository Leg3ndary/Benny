from email.mime import base
import time
import aiohttp
import asyncio
import discord
import datetime
import json
import os
from discord.ext import commands, ipc
from dotenv import load_dotenv
from gears import util
from gears.cprinter import InfoPrinter
import logging
import sys

load_dotenv()

start = time.monotonic()

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="Logs/discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
)
logger.addHandler(handler)

config = json.load(open("config.json"))

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
    presences=True,
    reactions=True,
    typing=False,
    voice_states=True,
    webhooks=True,
    message_content=True,
)


async def get_prefix(bot, msg) -> list:
    """
    Gets the prefix from built cache, if a guild isn't found (Direct Messages) assumes prefix is just pinging the bot

    Raises AttributeError when the cache isn't built so we just have this quick fix,
    the bot itself won't respond to anything until prefixes are built but this
    silences noisy errors.
    """
    prefixes = [f"<@!{bot.user.id}> ", f"<@{bot.user.id}> "]
    if bot.LOADED_PREFIXES:
        if not msg.guild:
            return prefixes.append(bot.prefix)
        else:
            return prefixes + bot.prefixes.get(str(msg.guild.id), "")
    else:
        return ""


bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    description="Benny Bot",
)
bot.START_TIME = datetime.datetime.now(datetime.timezone.utc)
bot.LOADED_PREFIXES = False
bot.MUSIC_ENABLED = True
bot.PREFIX = config.get("Bot").get("Prefix")
bot.PLATFORM = sys.platform


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
    elif ctx.author.id == bot.owner_id:
        return True
    return True


async def start_bot() -> None:
    """
    Start the bot with everything it needs
    """
    bot.printer = InfoPrinter(bot)
    await bot.printer.p_load("Printer")

    bot.config = config
    await bot.printer.p_load("Config")

    bot.util = util.BotUtil(bot)
    await bot.printer.p_load("Bot Util")

    file_list = {}
    total = 0

    for file in await bot.util.get_files():
        file_len = await bot.util.len_file(file)
        file_list[file] = file_len
        total += file_len
    file_list["total"] = total
    bot.file_list = file_list

    async def when_bot_ready():
        """
        On ready dispatch and print stuff
        """
        await bot.wait_until_ready()
        bot.dispatch("load_prefixes")
        bot.dispatch("connect_wavelink")
        bot.dispatch("load_sentinel_managers")
        await bot.printer.p_bot_update("LOGGED IN")

    async with bot:
        async with aiohttp.ClientSession() as main_session:
            async with aiohttp.ClientSession() as base_session:
                async with aiohttp.ClientSession() as sentinel_session:
                    async with aiohttp.ClientSession() as discordstatus_session:
                        bot.sessions = {
                            "main": main_session,
                            "base": base_session,
                            "sentinel": sentinel_session,
                            "discordstatus": discordstatus_session,
                        }
                        await bot.printer.p_connect("AIOHTTP Sessions")

                        await bot.util.load_cogs(os.listdir("Bot/cogs"))

                        end = time.monotonic()

                        await bot.printer.p_bot(
                            "",
                            f"Bot loaded in approximately {(round((end - start) * 1000, 2))/1000} seconds",
                        )

                        bot.loop.create_task(when_bot_ready())
                        # bot.ipc = ipc.Server(bot, secret_key=config.get("IPC").get("Secret"))
                        # bot.ipc.start()
                        await bot.start(bot.config.get("Bot").get("Token"))
    

if bot.PLATFORM.lower() == "linux":
    import uvloop
    uvloop.install()

asyncio.run(start_bot())
