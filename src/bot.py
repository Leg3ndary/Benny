from discord.ext import commands
import discord
import os
from dotenv import load_dotenv
from gears.useful import load_cogs
from discord_slash import SlashCommand

bot = commands.Bot(
    command_prefix="s",
    description="The coolest bot ever",
    Intents=discord.Intents.all()
)

slash = SlashCommand(bot)

load_cogs(bot, os.listdir("src/cogs"))

@bot.event
async def on_ready():
    """On ready tell us"""
    print(f"Bot {bot.user} logged in.")

load_dotenv()
bot.run(os.getenv("BotToken"))