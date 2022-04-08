import aioredis
import asyncio
import datetime
import os
from discord import app_commands
import discord
from discord.ext import commands


"""
await self.cache.set("Key", "Data") Set a key
value = await self.cache.get("Key")
"""


class DictionaryView(discord.ui.View):
    """
    Class for managing dictionarie views
    """

    def __init__(self, slash: bool):
        """
        ctx: The context object needed to delete the original message
        """
        self.ctx = None
        self.slash = slash
        super().__init__(timeout=60)

    @discord.ui.button(emoji="🗑️", label="Delete", style=discord.ButtonStyle.danger)
    async def button_callback(self, button, interaction):
        if not self.slash:
            await self.ctx.delete()
        else:
            await self.ctx.delete_original_message()
        await interaction.response.send_message("Message Deleted", ephemeral=True)

class Dictionary(commands.Cog):
    """
    Dictionary Cache Manager, so we don't spam requests and can reduce bandwidth, not really that 
    important in the end though.
    """

    def __init__(self, bot):
        self.api_url = "https://api.dictionaryapi.dev/api/v2/entries/en/"
        self.bot = bot

    async def cog_load(self):
        """
        On Cog load do some stuff"""
        await self.ready_cache()

    async def ready_cache(self):
        """
        Initialize cache
        """
        self.cache = await aioredis.from_url(
            "redis://redis-18564.c10.us-east-1-2.ec2.cloud.redislabs.com:18564",
            username="",
            password=os.getenv("Dict_Pass"),
            decode_responses=True,
        )
        await self.bot.printer.print_load("Dictionary Cache")

    async def fetch_word(self, word: str) -> dict:
        """
        Fetch a word from the api, will call it.

        Parameters
        ----------
        word: str
            The word to search up 

        Returns
        -------
        dict
        """
        async with self.bot.aiosession.get(
            f"{self.api_url}{word}"
        ) as request:
            if request.status != 200:
                print(
                    f"[ ERROR ] [{datetime.datetime.utcnow()}]\nError Code: {request.status}\n{await request.json()}"
                )
            return await request.json()

    async def get_word(self, word: str) -> dict:
        """
        Will check if the built cache has the word.
        
        If not will go fetch it because yes.
        """

    async def update_cache(self, word: str) -> dict:
        """"""
        pass

    @app_commands.command(
        name="define"
    )
    async def define_slash(self, interaction: discord.Interaction, word: str) -> None:
        """
        Define slash command
        """
        await interaction.response.send_message("Hello from top level command!")

    @commands.command(
        name="define",
        description="""Description of command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=["dict", "def"],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def define_cmd(self, ctx):
        """Define a word"""


async def setup(bot):
    await bot.add_cog(Dictionary(bot))