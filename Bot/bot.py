import asyncio
import datetime
import json
import logging
import os
import sys
import time

import aiohttp
import discord
from discord.ext import commands, ipc
from dotenv import load_dotenv
from gears import util, cooldowns

load_dotenv()

start = time.monotonic()

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="Logs/discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
)
logger.addHandler(handler)

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

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


async def get_prefix(_bot: commands.Bot, msg: discord.Message) -> list:
    """
    Gets the prefix from built cache, if a guild isn't found (Direct Messages) assumes
    prefix is just pinging the bot

    Raises AttributeError when the cache isn't built so we just have this quick fix,
    the bot itself won't respond to anything until prefixes are built but this
    silences noisy errors.
    """
    prefixes = [f"<@!{_bot.user.id}> ", f"<@{_bot.user.id}> "]
    if _bot.LOADED_PREFIXES:
        if not msg.guild:
            return prefixes.append(_bot.prefix)
        else:
            return prefixes + _bot.prefixes.get(str(msg.guild.id), "")
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
    async with bot:
        async with aiohttp.ClientSession() as blogger_session:
            bot.config = config

            bot.blogger = util.BotLogger(bot, blogger_session)
            await bot.blogger.load("BotLogger")

            await bot.blogger.load("Config")

            bot.util = util.BotUtil(bot)
            await bot.blogger.load("Bot Util")

            file_list = {}
            total = 0

            for file in await bot.util.get_files():
                file_len = await bot.util.len_file(file)
                file_list[file] = file_len
                total += file_len
            file_list["total"] = total
            bot.file_list = file_list
            
            bot.pcc = cooldowns.PremiumChecker(bot)
            bot.pcc.premium_list = []

            async def when_bot_ready():
                """
                On ready dispatch and print stuff
                """
                await bot.wait_until_ready()
                bot.dispatch("load_prefixes")
                bot.dispatch("connect_wavelink")
                bot.dispatch("load_sentinel_managers")
                bot.dispatch("initiate_all_tags")
                await bot.blogger.bot_update("LOGGED IN")

            async with aiohttp.ClientSession() as main_session:
                async with aiohttp.ClientSession() as base_session:
                    async with aiohttp.ClientSession() as sentinel_session:
                        async with aiohttp.ClientSession() as discordstatus_session:
                            async with aiohttp.ClientSession() as translate_session:
                                bot.sessions = {
                                    "main": main_session,
                                    "base": base_session,
                                    "sentinel": sentinel_session,
                                    "discordstatus": discordstatus_session,
                                    "blogger": blogger_session,
                                    "translate": translate_session,
                                }
                                await bot.blogger.connect("AIOHTTP Sessions")

                                await bot.util.load_cogs(os.listdir("Bot/cogs"))

                                end = time.monotonic()

                                total_load = (round((end - start) * 1000, 2)) / 1000

                                await bot.blogger.bot_info(
                                    "",
                                    f"Bot loaded in approximately {total_load} seconds",
                                )

                                bot.loop.create_task(when_bot_ready())
                                bot.ipc = ipc.Server(
                                    bot, secret_key=config.get("IPC").get("Secret")
                                )
                                bot.ipc.start()
                                await bot.start(bot.config.get("Bot").get("Token"))


if bot.PLATFORM.lower() == "linux":
    import uvloop

    uvloop.install()

asyncio.run(start_bot())
