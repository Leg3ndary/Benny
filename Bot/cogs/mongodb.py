import discord
import discord.utils
import os
from discord.ext import commands
from gears import style
from motor.motor_asyncio import AsyncIOMotorClient


class MongoDB(commands.Cog):
    """Unimportant cog ha L bozo ratio'd"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        """Load mongodb when dispatched"""
        mongo_uri = (
            self.bot.config.get("Mongo")
            .get("URL")
            .replace("<Username>", self.bot.config.get("Mongo").get("User"))
            .replace("<Password>", self.bot.config.get("Mongo").get("Pass"))
        )
        self.bot.mongo = AsyncIOMotorClient(mongo_uri)
        await self.bot.printer.print_connect("MONGODB")


async def setup(bot):
    await bot.add_cog(MongoDB(bot))
