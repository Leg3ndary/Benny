import asqlite
import asyncio
import discord
import discord.utils
from discord.ext import commands
from gears import style
import json


class WelcomeManager:
    """
    Managing welcoming and related things
    """

    def __init__(self, bot: commands.Bot, db: asqlite.Connection) -> None:
        """
        Init method
        """
        self.bot = bot
        self.db = db

    async def to_str(self, embed: discord.Embed) -> str:
        """
        Convert a discord embed object into a string to save to our db
        """
        await self.bot.loop.run_in_executor(None, json.dumps(), embed.to_dict())


class Welcome(commands.Cog):
    """
    Anything to deal with welcoming or leaving"""

    def __init__(self, bot: commands.Bot) -> None:
        """Init for the bot"""
        self.bot = bot
'''
    async def cog_load(self) -> None:
        """
        On cog load create a connection because
        """
        self.db: asqlite.Connection = await asqlite.connect("Databases/server.db")
        
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS welcome (
                guild   TEXT    NOT NULL
                                    PRIMARY KEY,
                welcome TEXT,
                leave   TEXT
            );
        """)


    async def cog_unload(self) -> None:
        """
        On cog unload, close connection
        """
        await self.db.close()
'''
    
    


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Welcome(bot))
