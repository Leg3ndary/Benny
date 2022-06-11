import datetime

from discord.ext import commands


class Jikan:
    """Presents ways to access the jikan api"""

    def __init__(self, bot: commands.Bot):
        """Initiation of our custom nice jikan class"""
        self.api_url = "https://api.jikan.moe/v4"
        self.session = bot.session.get("main")

    async def request_url(self, endpoint: str, parameters: dict = "") -> dict:
        """
        Request a url from the API with the given url and parameters

        Parameters
        ----------
        endpoint: str
            The endpoint that we need to request
        parameters: dict
            Leave empty if you don't want any extra params
            supply a dict and it will be automatically formatted.

        Returns
        -------
        dict
        """
        async with self.session.get(
            f"{self.api_url}{endpoint}{await self.to_url(parameters)}"
        ) as request:
            if request.status in [200, 400]:
                pass
            else:
                print(
                    f"[ERROR] [{datetime.datetime.utcnow()}]\nError Code: {request.status}\n{await request.json()}"
                )
            return await request.json()

    async def to_url(self, dictionary: dict) -> str:
        """
        Create a url string based off dict

        Parameters
        ----------
        dictionary: dict
            The dictionary with key pair values to string together

        Returns
        -------
        str
        """
        if not dictionary:
            url_link = ""
        if len(dictionary) == 1:
            url_link = f"?{list(dictionary.keys())[0]}={dictionary[list(dictionary.keys())[0]]}"
        elif len(dictionary) >= 2:
            url_link = f"?{list(dictionary.keys())[0]}={dictionary[list(dictionary.keys())[0]]}"
            value = 0
            for param in dictionary.keys():
                if value == 0:
                    value = 1
                else:
                    url_link = url_link + f"&{param}={dictionary[param]}"
        return url_link

    async def get_anime_by_id(self, id: str) -> dict:
        """
        Get an anime by its ID

        Parameters
        ----------
        id: str
            The id of the anime to search for

        Returns
        -------
        dict

        Query Parameters
        ----------------
        None

        Responses
        ---------
        200:
            Success
        400:
            Error: Bad Request
        """
        return await self.request_url(f"/anime/{id}")

    async def get_anime_characters(self, id: str) -> dict:
        """
        Get an animes characters

        Parameters
        ----------
        id: str
            The id of the anime to search for characters

        Returns
        -------
        dict

        Query Parameters
        ----------------
        None

        Responses
        ---------
        200:
            Success
        400:
            Error: Bad Request
        """
        return await self.request_url(f"/anime/{id}/characters")

    async def get_anime_staff(self, id: str) -> dict:
        """
        Get an animes staff

        Parameters
        ----------
        id: str
            The id of the anime to search for staff

        Returns
        -------
        dict

        Query Parameters
        ----------------
        None

        Responses
        ---------
        200:
            Success
        400:
            Error: Bad Request
        """
        return await self.request_url(f"/anime/{id}/staff")

    async def get_anime_episodes(self, id: str, parameters: dict = {}) -> dict:
        """
        Get an animes episodes

        Parameters
        ----------
        id: str
            The id of the anime to search for episodes
        parameters: dict
            A dict of parameters

        Returns
        -------
        dict

        Query Parameters
        ----------------
        page: int (Optional)
            The page number to return

        Responses
        ---------
        200:
            Success
        400:
            Error: Bad Request
        """
        return await self.request_url(f"/anime/{id}/episodes", parameters)

    async def get_anime_episodes_by_id(self, id: str, episode: str):
        """Return an episodes info

        Parameters
        ----------
        id: str
            The id of the anime to search for staff
        episode: str
            The episode number

        Returns
        -------
        dict

        Query Parameters
        ----------------
        None

        Responses
        ---------
        200:
            Success
        400:
            Error: Bad Request
        """
        return await self.request_url(f"/anime/{id}/episodes/{str(episode)}")

    async def get_anime_news(self, id: str, parameters: dict = {}):
        """Get an animes current news

        Parameters
        ----------
        id: str
            The id of the anime to search for episodes
        parameters: dict
            A dict of parameters

        Returns
        -------
        dict

        Query Parameters
        ------------------
        page: int (Optional)
            The page number to return

        Responses
        ---------
        200:
            Success
        400:
            Error: Bad Request
        """
        return await self.request_url(f"/anime/{id}/forum", parameters)

    async def get_anime_videos(self, id: str):
        """Get an animes related videos
        \nNo Params"""
        return await self.request_url(f"/anime/{id}/videos")

    async def get_anime_pictures(self, id: str):
        """Get an animes related pictures
        \nNo Params"""
        return await self.request_url(f"/anime/{id}/pictures")

    async def get_anime_statistics(self, id: str):
        """Get an animes statistics
        \nNo Params"""
        return await self.request_url(f"/anime/{id}/statistics")

    async def get_anime_more_info(self, id: str):
        """Get more info about an anime
        \nNo Params"""
        return await self.request_url(f"/anime/{id}/moreinfo")

    async def get_anime_recommendations(self, id: str):
        """Get an animes recommendations from other users
        \nNo Params"""
        return await self.request_url(f"/anime/{id}/recommendations")

    async def get_anime_user_updates(self, id: str, parameters=""):
        """Get a list of users who have updated something related to anime
        \npage - int"""
        return await self.request_url(f"/anime/{id}/userupdates", parameters)

    async def get_anime_reviews(self, id: str, parameters=""):
        """Get an animes reviews
        \npage - int"""
        return await self.request_url(f"/anime/{id}/reviews", parameters)

    async def get_anime_relations(self, id: str):
        """Get a list of related animes, eg adapation, side story
        \nNo Params"""
        return await self.request_url(f"/anime/{id}/relations")

    async def get_anime_themes(self, id: str):
        """Get an animes themes (Seems to be music)
        \nNo Params"""
        return await self.request_url(f"/anime/{id}/themes")

    async def get_anime_search(self, parameters):
        """Literally search for an anime :L
        \npage - int
        \nlimit - int
        \nq - Search string
        \ntype - tv, movie, ova, special, ona or music
        \nscore - 0 to 10
        \nstatus - airing, complete or upcoming
        \nrating - g, pg, pg13, r17, r or rx
        \nsfw - boolean
        \ngenres - pass multiple with comma separation
        \norder_by - mal_id, title, type, rating, start_date, end_date, episodes, score, scored_by, rank, popularity, member, favorites
        \nsort - desc or asc
        \nletter - singular letter matching
        \nproducer - use producer id"""
        return await self.request_url(f"/anime", parameters)

    """Character Methods"""

    async def get_character_by_id(self, id: str):
        """Get a character by its id
        \nNo Params"""
        return await self.request_url(f"/characters/{id}")

    async def get_character_anime(self, id: str):
        """Get a characters anime and what role he plays in it
        \nNo Params"""
        return await self.request_url(f"/characters/{id}/anime")

    async def get_character_manga(self, id: str):
        """Get a characters manga, basically anime
        \nNo Params"""
        return await self.request_url(f"/characters/{id}/manga")

    async def get_character_voice_actors(self, id: str):
        """Get a character voice actors
        \nNo Params"""
        return await self.request_url(f"/characters/{id}/voices")

    async def get_character_pictures(self, id: str):
        """Get some images of a character
        \nNo Params"""
        return await self.request_url(f"/characters/{id}/pictures")

    async def get_character_search(self, parameters):
        """Get a character
        \npage - int
        \nlimit - int
        \nq - Search string
        \norder_by - mal_id, name or favorites
        \nsort - desc or asc
        \nletter - singular letter matching"""
        return await self.request_url(f"/characters", parameters)
