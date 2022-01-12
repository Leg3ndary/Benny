import discord
import discord.utils
import os
from discord.ext import commands
from gears import style
from motor.motor_asyncio import AsyncIOMotorClient


class MongoDB(commands.Cog):
    """Basically everything related to mongodb goes here"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_load_mongodb(self):
        """Load mongodb when dispatched"""

        mongo_uri = (
            self.bot.config.get("Mongo")
            .get("URL")
            .replace("<Username>", self.bot.config.get("Mongo").get("User"))
            .replace("<Password>", os.getenv("Mongo_Pass"))
        )

        self.bot.mongo = AsyncIOMotorClient(mongo_uri)
        print("Loaded MongoDB")

        self.CommandStats = self.bot.mongo.CommandStats

    """
    Command Stats Document Schema
    
    {
        "_id": ObjectId("Stuff"),
        "command": "qualified_command name",
        "uses": int,
        "": ""
    }
    
    """

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """How we track all commands usage"""
        command = ctx.command.qualified_name
        collection = self.CommandStats["Uses"]
        document = await collection.find_one({"Command": command})


def setup(bot):
    bot.add_cog(MongoDB(bot))
