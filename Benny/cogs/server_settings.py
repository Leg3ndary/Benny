import aiosqlite
import asyncio
import discord
import discord.utils
from discord.ext import commands
from gears.style import c_get_color, c_get_emoji


"""
CREATE TABLE playlists(id integer NOT NULL, playlist_name text NOT NULL, songs text NOT NULL);

INSERT INTO tablename VALUES(values go here);
INSERT INTO playlists VALUES(id, playlist_name, songs);

SELECT * FROM playlists;

SELECT * FROM playlists WHERE id IS 1289739812739821;

ALTER TABLE playlists ADD COLUMN plays integer;

UPDATE playlists SET plays = 0 WHERE id=11111;

DELETE FROM playlists WHERE plays <= 1;
"""

"""
CREATE TABLE prefixes(server_id integer NOT NULL, prefix1 text DEFAULT , )

"""


class ServerSettings(commands.Cog):
    """Manage server settings like prefixes, welcome messages, etc"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        name="prefix",
        description="""Manage or view prefixes""",
        help="""NMot done""",
        brief="""also not done :eyes:""",
        usage="Usage",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    async def prefix_manage(self, ctx):
        """Command description"""

    @prefix_manage.command(
        name="CommandName",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        usage="Usage",
        aliases=["None"],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def my_command(self, ctx):
        """Command description"""



def setup(bot):
    bot.add_cog(ServerSettings(bot))
