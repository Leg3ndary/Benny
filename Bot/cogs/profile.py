import asqlite
import discord
import discord.utils
from discord.ext import commands
from gears import style


class ProfileView(discord.ui.View):
    """Class for a user's profile"""
    def __init__(self):
        super().__init__()

class Profile(commands.Cog):
    """Profile Cog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_load_profiles(self):
        """Load profile db"""
        async with asqlite.connect("Databases/profile.db") as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS profiles (
                    id               TEXT PRIMARY KEY
                                    NOT NULL,
                    name             TEXT NOT NULL,
                    main_description TEXT,
                    main_image       TEXT
                );
                """
            )
        await self.bot.printer.print_load("Profiles")

def setup(bot):
    bot.add_cog(Profile(bot))
