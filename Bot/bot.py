import aiohttp
import asyncio
import discord
import json
import os
import time
from discord.ext import commands
from dotenv import load_dotenv
from gears import util
from gears.info_printer import InfoPrinter


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
    integrations=True,
    invites=True,
    members=True,
    messages=True,
    presences=True,
    reactions=True,
    typing=False,
    voice_states=True,
    webhooks=True,
)

prefix = config.get("Bot").get("Prefix")

async def get_prefix(bot, msg):
    """Gets the prefix from built cache, if a guild isn't found (Direct Messages) assumes prefix is the below"""
    if msg.guild is None:
        return bot.prefix
    else:
        return bot.prefixes[str(msg.guild.id)]


async def start_bot():
    """Start the bot with a session"""
    start = time.monotonic()

    bot = commands.Bot(
        command_prefix=get_prefix, intents=intents, description="The coolest bot ever"
    )

    bot.printer = InfoPrinter()
    await bot.printer.print_load("Printer")

    bot.config = config
    await bot.printer.print_load("Config")

    bot.prefix = prefix

    util.load_cogs(bot, os.listdir("Bot/cogs"))

    @bot.event
    async def on_ready():
        """On ready tell us"""
        bot.dispatch("load_musicdb")
        bot.dispatch("load_playlists")
        bot.dispatch("load_mongodb")
        bot.dispatch("load_prefixes")
        print(f"Bot {bot.user} logged in.")

    async with aiohttp.ClientSession() as session:
        bot.aiosession = session
        print("Loaded aiohttp session")

        await bot.start(os.getenv("Bot_Token"))


asyncio.run(start_bot())
