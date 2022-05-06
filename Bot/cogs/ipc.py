from discord.ext import commands, ipc


class IpcRoutes(commands.Cog):
    """
    IPC Related stuff
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ipc_ready(self):
        """Called upon the IPC Server being ready"""
        await self.bot.printer.p_connect("IPC")

    @ipc.server.route()
    async def test_endpoint(self, data):
        guild = self.bot.get_guild(data.guild_id)

        return guild.member_count


async def setup(bot):
    await bot.add_cog(IpcRoutes(bot))
