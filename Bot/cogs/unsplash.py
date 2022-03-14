import aiohttp
import os
from discord.ext import commands


param_dict = {"images": ""}


class UnsplashClient:
    """Accessing unsplash"""

    def __init__(self):
        self.auth = {"Authorization": f"Client-ID {os.getenv('Unsplash_Access')}"}
        self.session = aiohttp.ClientSession(
            base_url="https://api.unsplash.com", headers=self.auth
        )
        self.latest_header = None

    """Cache for latest save data from unsplash NOT FINISHED"""

    async def set_latest_header(self, header):
        """Set the latest header"""
        self.latest_header = header

    async def get_ratelimit_remaining(self):
        """Get rate limit remaining on requests"""
        return self.latest_header.get("X-Ratelimit-Remaining", -1)

    """Regular methods"""

    async def get_random_photo(self, params: dict = {}):
        """Get a completely random photo from unsplash"""
        request_string = await self.to_url(params)
        return await self.request_url(f"""/photos/random/{request_string}""")

    async def get_photo_by_id(self, photo_id: str):
        """Get a photo by its id"""
        return await self.request_url(f"""/photos/{photo_id}/""")

    async def get_user_profile(self, username: str):
        """Return a public users profile information"""
        return await self.request_url(f"""/users/{username}/""")

    async def get_user_portfolio(self, username: str):
        """Return a public users portfolio link"""
        return await self.request_url(f"""/users/{username}/portfolio/""")

    async def get_user_photos(self, username: str, params: dict):
        """Returns a list of all the users photos"""
        request_url = await self.to_url(params)
        return await self.request_url(f"""/users/{username}/photos/{request_url}""")

    async def get_user_liked_photos(self, username: str, params: dict):
        """Returns a list of all the photos a user has liked"""
        request_url = await self.to_url(params)
        return await self.request_url(f"""/users/{username}/likes/{request_url}""")

    async def get_user_collections(self, username: str, params: dict):
        """Returns a list of all the collections a user has made"""
        request_url = await self.to_url(params)
        return await self.request_url(
            f"""/users/{username}/collections/{request_url}"""
        )

    async def get_user_statistics(self, username: str, params: dict):
        """Return a users statistics"""
        request_url = await self.to_url(params)
        return await self.request_url(f"""/users/{username}/statistics/{request_url}""")

    async def search_photos(self, params: dict):
        """Search for photos based on the params given"""
        request_url = await self.to_url(params)
        return await self.request_url(f"""/search/photos/{request_url}""")

    async def search_collections(self, params: dict):
        """Search for collections based on the params given"""
        request_url = await self.to_url(params)
        return await self.request_url(f"""/search/collections/{request_url}""")

    async def search_users(self, params: dict):
        """Search for users based on the params given"""
        request_url = await self.to_url(params)
        return await self.request_url(f"""/search/users/{request_url}""")

    async def get_total_stats(self):
        """Return total Unsplash stats"""
        return await self.request_url(f"""/stats/total""")

    async def get_monthly_stats(self):
        """Return monthly counts (30 days)"""
        return await self.request_url(f"""/stats/month""")

    # Requesting stuff
    async def to_url(self, dictionary: dict):
        """Create a url string based off dict"""
        if not dictionary:
            url_link = ""
        if len(dictionary) == 1:
            url_link = f"?{dictionary.keys()[0]}={dictionary[dictionary.keys()[0]]}"
        elif len(dictionary) >= 2:
            url_link = f"?{dictionary.keys()[0]}={dictionary[dictionary.keys()[0]]}"
            value = 0
            for param in dictionary.keys():
                if value == 0:
                    value = 1
                else:
                    url_link = url_link + f"&{param}={dictionary[param]}"

        return url_link

    async def request_url(self, url: str):
        """Get a url and update latest header"""
        request = await self.session.get(self.api_url + url)
        await self.set_latest_header(request.headers)
        return await request.json()

    async def get_param(self, method: str):
        """Return possible parameters from methods"""
        return param_dict.get(method)


class Photos(commands.Cog):
    """Everything to do with photos!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="photo",
        description="""photo searching stuff""",
        help="""Search for photos based on queries""",
        brief="Search for photos",
        aliases=[],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def photo_cmd(self, ctx):
        """Command description"""



async def setup(bot):
    await bot.add_cog(Photos(bot))
