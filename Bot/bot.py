import aiohttp
import asyncio
from colorama import Fore
import discord
import math
import json
import os
import time
from discord.ext import commands
from dotenv import load_dotenv
from gears import util, style
from gears.info_printer import InfoPrinter

start = time.monotonic()

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
    """
    Start the bot with everything it needs
    """
    bot = commands.Bot(
        command_prefix=get_prefix, intents=intents, description="The coolest bot ever"
    )

    bot.printer = InfoPrinter(bot)
    await bot.printer.print_load("Printer")

    bot.config = config
    await bot.printer.print_load("Config")

    bot.prefix = prefix

    bot.util = util.BotUtil(bot)
    await bot.printer.print_load("Bot Util")

    file_list = {}
    total = 0

    for file in await bot.util.get_files():
        file_len = await bot.util.len_file(file)
        file_list[file] = file_len
        total += file_len
    file_list["total"] = total
    bot.file_list = file_list

    await bot.util.load_cogs(os.listdir("Bot/cogs"))

    @bot.event
    async def on_ready():
        """
        On ready dispatch and print stuff
        """
        bot.dispatch("load_musicdb")
        bot.dispatch("load_playlists")
        bot.dispatch("load_mongodb")
        bot.dispatch("load_prefixes")
        await bot.printer.print_bot_update("LOGGED IN")

    @bot.event
    async def on_guild_join(guild):
        """
        When we join a guild print it out
        """
        guild_bots = 0
        for member in guild.members:
            if member.bot:
                guild_bots += 1

        humans = len(guild.members) - guild_bots

        bot_percentage = math.trunc((guild_bots / len(guild.members)) * 10000) / 100

        await bot.printer.print_bot(
            await bot.printer.generate_category(f"{Fore.GREEN}JOINED"),
            f" {guild.name} {guild.id} | Server is {bot_percentage}% Bots ({guild_bots}/{len(guild.members)})",
        )

        if bot_percentage > 20 and humans < 19:
            sent = False
            embed = discord.Embed(
                title=f"Sorry!",
                description=f"""Your server has **{guild_bots} Bots ** compared to **{len(guild.members)} Members**
                Either:
                - Have `20+` humans
                Currently **{humans}** humans
                - Lower your servers percentage of bots to under 20%
                Currently **{bot_percentage}%** bots""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            for channel in guild.channels:
                if "general" in channel.name:
                    await channel.send(embed=embed)
                    sent = True
                    break
            if not sent:
                try:
                    await guild.channels[0].send(embed=embed)
                except:
                    pass
            await guild.leave()
            await bot.printer.print_bot(
                await bot.printer.generate_category(f"{Fore.MAGENTA}AUTOLEFT"),
                f" {guild.name} {guild.id}",
            )

    @bot.event
    async def on_guild_remove(guild):
        """
        When we leave a guild
        """
        await bot.printer.print_bot(
            await bot.printer.generate_category(f"{Fore.RED}LEFT"),
            f" {guild.name} {guild.id}",
        )

    @bot.check
    async def global_check(ctx):
        """
        Global check that applies to all commands
        ├─ Check if its me, so I bypass everything
        ├─ Check if the user is blacklisted from the bot
        ├─ Check if command is disabled
        ├─ Check if channel/thread is being ignored
        ├─
        ├─
        └─
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
        await bot.start(os.getenv("Bot_Token"))


asyncio.run(start_bot())
