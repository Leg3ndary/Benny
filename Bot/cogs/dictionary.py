import datetime

import discord
from discord.ext import commands
from gears import style
from motor.motor_asyncio import AsyncIOMotorClient


class DictDropdown(discord.ui.Select):
    """
    Dict Dropdown
    """

    def __init__(self, entries: list) -> None:
        """
        Init the dict dropdown
        """
        self.entries = entries[:25]

        options = []

        for entry in entries:
            options.append(
                discord.SelectOption(
                    label="Red", description="Your favourite colour is red"
                )
            )

        super().__init__(
            placeholder="Choose a word to define",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        await interaction.response.send_message(
            f"Your favourite colour is {self.values[0]}"
        )


class DictionaryMenu(discord.ui.View):
    """
    Dictionary Menu
    """

    def __init__(self, entries) -> None:
        """
        Initiative it
        """
        super().__init__()
        self.entries = entries
        self.add_item(DictDropdown())


class WordNotFound(Exception):
    """
    Raised when a word isn't found
    """


class Dictionary(commands.Cog):
    """
    Dictionary Cache Manager, so we don't spam requests and can reduce bandwidth, not really that
    important in the end though.
    """

    COLOR = style.Color.MAROON
    ICON = ":books:"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init the dictionary cog
        """
        self.api_url = "https://api.dictionaryapi.dev/api/v2/entries/en/"
        self.bot = bot
        self.session = bot.sessions.get("main")

    async def cog_load(self) -> None:
        """
        On Cog load do some stuff
        """
        mongo_uri = (
            self.bot.config.get("Dictionary")
            .get("URL")
            .replace("<Username>", self.bot.config.get("Dictionary").get("User"))
            .replace("<Password>", self.bot.config.get("Dictionary").get("Pass"))
        )
        self.con = AsyncIOMotorClient(mongo_uri)
        self.db = self.con["Dictionary"]
        self.dict = self.db["Dict"]
        await self.bot.blogger.connect("DICTIONARY MONGO")

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
        async with self.session.get(f"{self.api_url}{word}") as request:
            new_data = await request.json()
            if request.status == 404:
                raise WordNotFound(f"Sorry but the word: {word}, has not been found")
            if request.status == 200:
                self.bot.loop.create_task(self.update_dict(word, new_data))
            else:
                print(
                    f"[ ERROR ] [{datetime.datetime.utcnow()}]\nError Code: {request.status}\n{await request.json()}"
                )
            return new_data

    async def get_word(self, word: str) -> dict:
        """
        Will check if the db has the word.

        If not will go fetch it because yes.
        """
        search = {"_id": word}
        result = await self.dict.find_one(search)

        if not result:
            result = await self.fetch_word(word)

        return result

    async def update_dict(self, word: str, data: dict) -> None:
        """
        Update the cache with the correct data
        """
        entry = {"_id": word, "data": data}
        await self.dict.replace_one(entry, upsert=True)

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
    async def define_cmd(self, ctx: commands.Context, *, word: str) -> None:
        """Define a word"""
        data = await self.get_word(word)
        await ctx.send("Sorry, this command doesn't actually do anything as of now")


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Dictionary(bot))
