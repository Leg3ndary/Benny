import time
import aiohttp
import asqlite
import asyncio
import discord
import datetime
import json
import os
from discord.ext import commands
from dotenv import load_dotenv
from gears import util
from gears.info_printer import InfoPrinter
import logging


start = time.monotonic()

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="logs/discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
)
logger.addHandler(handler)

load_dotenv()

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

prefix = config.get("Bot").get("Prefix")


async def get_prefix(bot, msg):
    """Gets the prefix from built cache, if a guild isn't found (Direct Messages) assumes prefix is the below"""
    if msg.guild is None:
        return bot.prefix
    else:
        return bot.prefixes.get(str(msg.guild.id))


bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    description="Benny Bot, a cool bot obviously",
)
bot.start_time = datetime.datetime.now(datetime.timezone.utc)


async def start_bot():
    """
    Start the bot with everything it needs
    """
    async with bot:
        bot.MUSIC_ON = True

        bot.printer = InfoPrinter(bot)
        await bot.printer.print_load("Printer")

        bot.config = config
        await bot.printer.print_load("Config")

        bot.prefix = prefix

        bot.util = util.BotUtil(bot)
        await bot.printer.print_load("Bot Util")

        bot.settingsDB = await asqlite.connect("Databases/server.db")
        await bot.printer.print_connect("Settings Database")

        bot.musicDB = await asqlite.connect("Databases/music.db")
        await bot.printer.print_connect("Music Database")

        file_list = {}
        total = 0

        for file in await bot.util.get_files():
            file_len = await bot.util.len_file(file)
            file_list[file] = file_len
            total += file_len
        file_list["total"] = total
        bot.file_list = file_list

        await bot.util.load_cogs(os.listdir("Bot/cogs"))

        async def when_bot_ready():
            """
            On ready dispatch and print stuff
            """
            await bot.wait_until_ready()
            bot.dispatch("load_prefixes")
            await bot.tree.sync(guild=discord.Object(id=839605885700669441))
            await bot.printer.print_bot_update("LOGGED IN")

        @bot.check
        async def global_check(ctx):
            """
            Global check that applies to all commands
            ├─ Check if its me, so I bypass everything
            ├── Check if the user is blacklisted from the bot
            ├─── Check if command is disabled
            ├──── Check if channel/thread is being ignored
            ├─────
            ├──────
            └───────
            """
            return True

        async with aiohttp.ClientSession() as session:
            bot.aiosession = session
            await bot.printer.print_connect("AIOHTTP Session")
            end = time.monotonic()
            await bot.printer.print_bot(
                "",
                f"Bot loaded in approximately {(round((end - start) * 1000, 2))/1000} seconds",
            )
            bot.loop.create_task(when_bot_ready())
            await bot.start(os.getenv("Bot_Token"))


asyncio.run(start_bot())
