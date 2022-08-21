import discord
from discord.ext import commands
from gears import dictapi, style


class DictDropdown(discord.ui.Select):
    """
    Dict Dropdown
    """

    def __init__(self, word: dictapi.Word) -> None:
        """
        Init the dict dropdown
        """
        self.word = word
        self.meanings = list(word.meanings)[:25]

        options = []

        for counter, meaning in enumerate(self.meanings):
            options.append(
                discord.SelectOption(
                    label=meaning.part_of_speech,
                    description=f"{meaning.definitions[0].definition[:47]}..."
                    if len(meaning.definitions[0].definition) > 50
                    else meaning.definitions[0].definition,
                    value=counter,
                )
            )

        super().__init__(
            placeholder="Choose a Meaning to View",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """
        Select a word to define
        """
        meaning = self.meanings[int(self.values[0])]

        embed = discord.Embed(
            title=f"{self.word.word} Definition",
            url=self.word.phonetics[0].audio if self.word.phonetics[0].audio else None,
            timestamp=discord.utils.utcnow(),
            color=style.Color.MAROON,
        )
        embed.add_field(
            name="Part of Speech", value=meaning.part_of_speech, inline=False
        )
        embed.add_field(
            name="Definition",
            value=f"{meaning.definitions[0].definition}\n>>> {meaning.definitions[0].example if meaning.definitions[0].example else 'No Example'}",
            inline=False,
        )
        embed.set_author(
            name=f"License: {self.word.license.name}",
            url=self.word.license.url,
        )
        embed.set_footer(
            text=f"Meaning {int(self.values[0]) + 1}/{len(self.word.meanings)}"
        )
        await interaction.response.edit_message(embed=embed, view=self.view)


class DictionaryMenu(discord.ui.View):
    """
    Dictionary Menu
    """

    def __init__(self, word: dictapi.Word) -> None:
        """
        Initiative it
        """
        super().__init__()
        self.add_item(DictDropdown(word))


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
        self.bot = bot
        self.dc: dictapi.DictClient = dictapi.DictClient(bot.sessions.get("main"))

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
        """
        Define a word
        """
        if not word.isalpha():
            raise commands.BadArgument(
                "The requested definition must be alphabetic, this means no spaces or special characters"
            )

        data = await self.dc.fetch_word(word)
        status = data.get("status")
        json = data.get("data")

        if status == 200:
            word = dictapi.Word(json[0])

            embed = discord.Embed(
                title=f"{word.word} Definition",
                description="""Select one of the below to view different meanings of the word.""",
                url=word.phonetics[0].audio if word.phonetics[0].audio else None,
                timestamp=discord.utils.utcnow(),
                color=style.Color.MAROON,
            )
            embed.set_author(
                name=f"License: {word.license.name}",
                url=word.license.url,
            )
            embed.set_footer(text=f"Meaning -/{len(word.meanings)}")
            await ctx.send(embed=embed, view=DictionaryMenu(word))


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Dictionary(bot))
