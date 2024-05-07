"""
A small dataclass I made for a dictionary api
"""

from typing import Any, Dict, Tuple

import aiohttp
import discord
from discord.ext import commands

from . import style


class License:
    """
    A license
    """

    __slots__ = ("name", "url")

    def __init__(self, data: Dict[str, Any]) -> None:
        """
        Construct the license
        """
        self.name: str = data.get("name", "N/A")
        self.url: str = data.get("url", "N/A")


class Phonetic:
    """
    A phonetic and related data
    """

    __slots__ = ("text", "audio", "source", "license")

    def __init__(self, data: Dict[str, Any]) -> None:
        """
        Construct the phonetic
        """
        self.text: str = data.get("text", "")
        self.audio: str = data.get("audio", "")
        self.source: str = data.get("sourceUrl", "")
        self.license: License = data.get("license", "")


class Definition:
    """
    A words definition
    """

    __slots__ = ("definition", "example", "synonyms", "antonyms")

    def __init__(self, data: Dict[str, Any]) -> None:
        self.definition: str = data.get("definition", "")
        self.example: str = data.get("example", "")
        self.synonyms: Tuple[str] = tuple(data.get("synonyms", ()))
        self.antonyms: Tuple[str] = tuple(data.get("antonyms", ()))


class Meaning:
    """
    A words's meaning, lol
    """

    __slots__ = ("part_of_speech", "definitions", "synonyms", "antonyms")

    def __init__(self, data: Dict[str, Any]) -> None:
        """
        42.
        """
        self.part_of_speech: str = data.get("partOfSpeech", "N/A")
        self.definitions: Tuple[Definition] = tuple(
            Definition(definition) for definition in data.get("definitions", ())
        )
        self.synonyms: Tuple[str] = tuple(data.get("synonyms", ()))
        self.antonyms: Tuple[str] = tuple(data.get("antonyms", ()))


class Word:
    """
    A word with relevant data...
    """

    __slots__ = (
        "word",
        "phonetics",
        "meanings",
        "synonyms",
        "antonyms",
        "license",
        "sources",
    )

    def __init__(self, data: Dict[str, Any]) -> None:
        """
        Construct the word
        """
        self.word: str = data.get("word", None)
        self.phonetics: Tuple[Phonetic] = tuple(
            Phonetic(phonetic) for phonetic in data.get("phonetics", ())
        )
        self.meanings: Tuple[Meaning] = tuple(
            Meaning(meaning) for meaning in data.get("meanings", ())
        )
        self.synonyms: Tuple[str] = data.get("synonyms", ())
        self.antonyms: Tuple[str] = data.get("antonyms", ())
        self.license: License = License(data.get("license", {}))
        self.sources: Tuple[str] = tuple(data.get("sources", ()))


class DictClient:
    """
    Client to access the dict api
    """

    API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """
        Construct the client
        """
        self.session = session

    async def fetch_word(self, word: str) -> Dict[str, Any]:
        """
        Fetch a word
        """
        async with self.session.get(f"{self.API_URL}{word}") as response:
            return {"status": response.status, "data": await response.json()}


class DictDropdown(discord.ui.Select):
    """
    Dict Dropdown
    """

    def __init__(self, word: Word) -> None:
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
                    description=(
                        f"{meaning.definitions[0].definition[:47]}..."
                        if len(meaning.definitions[0].definition) > 50
                        else meaning.definitions[0].definition
                    ),
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

    def __init__(self, ctx: commands.Context, word: Word) -> None:
        """
        Initiative it
        """
        super().__init__()
        self.ctx = ctx
        self.add_item(DictDropdown(word))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        If the interaction isn't by the user, return a fail.
        """
        if interaction.user != self.ctx.author:
            return False
        return True
