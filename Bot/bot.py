import aiohttp
import asyncio
import discord
import json
import os
from discord.ext import commands
from dotenv import load_dotenv
from gears import util


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

async def get_prefix(bot, message):
    """Gets the prefix from built cache, if a guild isn't found (Direct Messages) assumes prefix is the below"""
    if message.guild is None:
        return bot.prefix
    else:
        return bot.prefix_cache[str(message.guild.id)]


async def start_bot():
    """Start the bot with a session"""
    bot = commands.Bot(
        command_prefix=prefix, intents=intents, description="The coolest bot ever"
    )

    bot.config = config
    print("Loaded Bot Config")

    bot.prefix = prefix
    print("Loaded default prefix")

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
