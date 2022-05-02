from motor.motor_asyncio import AsyncIOMotorClient
import datetime
import discord
from discord.ext import commands, tasks


class DictionaryView(discord.ui.View):
    """
    Class for managing dictionary views
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
        On Cog load do some stuff
        """
        mongo_uri = (
            self.bot.config.get("Dictionary").get("URL")
            .replace("<Username>", self.bot.config.get("Dictionary").get("User"))
            .replace("<Password>", self.bot.config.get("Dictionary").get("Pass"))
        )
        self.bot.mongo = AsyncIOMotorClient(mongo_uri)
        await self.bot.printer.print_connect("MONGODB")

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
        async with self.bot.aiosession.get(f"{self.api_url}{word}") as request:
            new_data = await request.json()
            print(new_data)
            if request.status != 200:
                print(
                    f"[ ERROR ] [{datetime.datetime.utcnow()}]\nError Code: {request.status}\n{await request.json()}"
                )
            else:
                self.bot.loop.create_task(self.update_cache(word, new_data))
            return new_data

    async def get_word(self, word: str) -> dict:
        """
        Will check if the built cache has the word.

        If not will go fetch it because yes.
        """
        result = await self.cache.get(word)

        if not result:
            await self.fetch_word(word)

    async def update_cache(self, word: str, data: dict) -> None:
        """
        Update the cache with the correct data"""
        await self.cache.set(word, str(data))

    @commands.hybrid_command(
        name="define",
        description="""Get a words amazing definition""",
        help="""Define a word""",
        brief="Define a word",
        aliases=["dict", "def"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def define_cmd(self, ctx, *, word: str):
        """Define a word"""
        data = await self.get_word(str(word))
        await ctx.send(data)

async def setup(bot):
    await bot.add_cog(Dictionary(bot))
