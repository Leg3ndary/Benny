from discord.ext import commands, ipc


class IpcRoutes(commands.Cog):
    """
    IPC Related stuff
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ipc_ready(self):
        """Called upon the IPC Server being ready"""
        await self.bot.blogger.connect("IPC")

    @ipc.server.route()
    async def len_bot_guilds(self):
        """
        Amount of guilds the bot is in
        """
        return len(self.bot.guilds)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(IpcRoutes(bot))
