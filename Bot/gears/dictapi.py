"""
A small dataclass I made for a dictionary api
"""

from typing import Any, Dict, Tuple

import aiohttp


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
        self.definitions: Tuple[Definition] = (
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
        self.phonetics: Tuple[Phonetic] = (
            Phonetic(phonetic) for phonetic in data.get("phonetics", ())
        )
        self.meanings: Tuple[Meaning] = (
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

    async def fetch_word(self, word: str) -> None:
        """
        Fetch a word
        """
        async with self.session.get(f"{self.API_URL}{word}") as response:
            return response.status, await response.json()
