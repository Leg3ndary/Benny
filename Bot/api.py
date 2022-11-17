from aiohttp import web
from discord.ext import commands


class BotApp(web.Application):
    """
    The Bot Application
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init"""
        super().__init__()
        self.bot = bot
        self.add_routes([web.get("/", self.home)])
        self.add_routes([web.get("/ping", self.ping)])

    async def home(self, request: web.Request) -> web.Response:
        """
        Home page
        """
        return web.json_response({"Api": "Alive"})

    async def ping(self, request: web.Request) -> web.Response:
        """
        Ping the bot
        """
        return web.json_response({"status": "ok", "latency": self.bot.latency})

    async def start(self, host: str, port: int) -> None:
        """
        Start the bot app
        """
        runner = web.AppRunner(self)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
