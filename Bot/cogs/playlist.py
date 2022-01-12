import aiosqlite
import asyncio
import discord
import discord.utils
from discord.ext import commands
from gears import style


"""

CREATE TABLE IF NOT EXISTS playlists(id integer NOT NULL, name text NOT NULL, plays integer NOT NULL, songs text);
INSERT INTO playlists VALUES(1, "playlistttt", 0, "");
INSERT INTO playlists VALUES(3, "another playlist", 0, "song, song2, song33333333");
INSERT INTO playlists VALUES(1235551, "somethingelse", 5, "i like it like that, sdasdasd");
CREATE TABLE IF NOT EXISTS playlists(id integer NOT NULL, name text NOT NULL, plays integer NOT NULL, songs text);

INSERT INTO tablename VALUES(values go here);
INSERT INTO playlists VALUES(id, playlist_name, songs);

SELECT * FROM playlists;

SELECT * FROM playlists WHERE id IS 1289739812739821;

ALTER TABLE playlists ADD COLUMN plays integer;

UPDATE playlists SET plays = 0 WHERE id=11111;

DELETE FROM playlists WHERE plays <= 1;

cursor.execute("SELECT * FROM table_name WHERE value = ?", ('peepeepoopoo',))
"""


class PlaylistManager:
    """
    Bunch of methods to interact with and update/delete playlists

    Attributes
    ----------
    PLAYLIST_SONG_LIMIT: int
        The max no of songs that a playlist may have
    PLAYLIST_LIMIT: int
        The max no of playlists that a user may have under an ID
    SONG_NAME_LIMIT:
        The max length of a song name in chars
    """

    def __init__(self) -> None:
        """Constructs all the necessary attributes for the PlaylistManager"""
        self.PLAYLIST_SONG_LIMIT = 150
        self.PLAYLIST_LIMIT = 5
        self.SONG_NAME_LIMIT = 50

    async def create_playlist(self, user_id: int, playlist_name: str) -> str:
        """
        Create a playlist in our database

        Parameters
        ----------
        user_id: int
            The users ID
        playlist_name: str
            The name to call the playlist

        Returns
        -------
        str

        SUCCESS:
            Succeeded
        ERROR:
            Errored, .split(":")[1] will get you the reason
        """
        async with aiosqlite.connect("music.db") as db:
            async with db.execute(
                """SELECT id FROM playlists WHERE id = ?;""", (int(user_id),)
            ) as cursor:
                length = len(await cursor.fetchall())
                if length > self.PLAYLIST_LIMIT:
                    return f"ERROR:You can only create {self.PLAYLIST_LIMIT} playlists!"

            await db.execute(
                """INSERT INTO playlists VALUES(?, ?, 0, "");""",
                (user_id, playlist_name),
            )
            await db.commit()
            return "SUCCESS"

    async def delete_playlist(self, user_id: int, playlist_name: str) -> str:
        """
        Delete a playlist in our database

        Parameters
        ----------
        user_id: int
            The users ID
        playlist_name: str
            The name of the playlist to delete

        Returns
        -------
        str

        SUCCESS:
            Succeeded
        ERROR:
            Errored, .split(":")[1] will get you the reason
        """
        async with aiosqlite.connect("music.db") as db:
            async with db.execute(
                """SELECT id, name FROM playlists WHERE id = ? and name = ?;""",
                (int(user_id), playlist_name),
            ) as cursor:
                if not cursor.fetchall():
                    return (
                        f"ERROR:No playlist by the name of {playlist_name} was found!"
                    )
            await db.execute(
                """DELETE FROM playlists WHERE name = ?;""", (playlist_name,)
            )
            await db.commit()
            return "SUCCESS"

    async def add_song(self, user_id: int, playlist_name: str, song: str) -> str:
        """
        Add a song to a playlist by ID

        Parameters
        ----------
        user_id: int
            The users ID
        playlist_name: str
            The name of the playlist
        song: str
            The song/query that will be added to the playlist

        Returns
        -------
        str

        SUCCESS:
            Succeeded
        ERROR:
            Errored, .split(":")[1] will get you the reason
        """
        # Cleaning out commas in which we use as delimiters.
        song = song.replace(",", "")

        if len(song) > self.SONG_NAME_LIMIT:
            return f"ERROR:Please limit the song name to 50 characters ({self.SONG_NAME_LIMIT} currently)"

        async with aiosqlite.connect("music.db") as db:
            async with db.execute(
                """SELECT * FROM playlists WHERE id = ? AND name = ?""",
                (int(user_id), playlist_name),
            ) as cursor:
                if not await cursor.fetch():
                    return f"ERROR:You have no playlists named {playlist_name}!"
                else:
                    # Songs index is no 3
                    data = await cursor.fetch()
                    songs_length = data[3].count(", ")
                    if (songs_length + 1) > self.PLAYLIST_SONG_LIMIT:
                        return f"ERROR:You have reached the max amount of songs ({self.PLAYLIST_SONG_LIMIT})"
                    elif songs_length == 0:
                        prefix = ""
                    else:
                        prefix = ", "
            await db.execute(
                f"""INSERT INTO playlists VALUES(?, ?, ?, ?);""",
                (data[0], data[1], data[2], data[4].append(prefix + song)),
            )
            await db.commit()
            return f"SUCCESS"

    async def delete_song(self, user_id: int, playlist_name: str, song_index) -> str:
        """
        Add a song to a playlist by ID

        Parameters
        ----------
        user_id: int
            The users ID
        playlist_name: str
            The name of the playlist
        song_index: str
            The song/index that will be removed from the playlist
            If a str, then will search for it in the playlist and remove.
            If an index, will only remove that index
        NOT DONE
        Returns
        -------
        str

        SUCCESS:
            Succeeded
        ERROR:
            Errored, .split(":")[1] will get you the reason
        """
        # Cleaning out commas in which we use as delimiters.
        song_index = song_index.replace(",", "")

        if song_index.is_numeric() and song_index > self.PLAYLIST_SONG_LIMIT:
            return f"ERROR:Max"

        async with aiosqlite.connect("music.db") as db:
            async with db.execute(
                """SELECT * FROM playlists WHERE id = ? AND name = ?""",
                (int(user_id), playlist_name),
            ) as cursor:
                if not await cursor.fetch():
                    return f"ERROR:You have no playlists named {playlist_name}!"
                else:
                    # Songs index is no 3
                    data = await cursor.fetch()
                    songs_length = data[3].count(", ")
                    if (songs_length + 1) > self.PLAYLIST_SONG_LIMIT:
                        return f"ERROR:You have reached the max amount of songs ({self.PLAYLIST_SONG_LIMIT})"
                    elif songs_length == 0:
                        prefix = ""
                    else:
                        prefix = ", "
            await db.execute(
                f"""DELETE FROM playlists WHERE id = ?, ?, ?, ?);""",
                (data[0], data[1], data[2], data[4].append(prefix)),
            )
            await db.commit()
            return f"SUCCESS"

    async def get_playlists(self, user_id: int) -> list:
        """
        Get a list of all of a user's playlists and info about them...

        Parameters
        ----------
        user_id:
            The users ID

        Returns
        -------
        list
        """
        async with aiosqlite.connect("music.db") as db:
            async with db.execute(
                """SELECT * FROM playlists WHERE id = ?;""", (int(user_id),)
            ) as cursor:
                playlists = await cursor.fetchall()
                return playlists


class Playlist(commands.Cog):
    """Manage and view playlists which you can also use to interact and listen too"""

    def __init__(self, bot):
        self.bot = bot
        self.playlistmanager = PlaylistManager()

    @commands.Cog.listener()
    async def on_load_playlists(self):
        """Load up playlist related stuff"""
        async with aiosqlite.connect("music.db") as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS playlists(id integer NOT NULL, name text NOT NULL, plays integer NOT NULL, songs text);"""
            )
        print("Playlists Table Loaded")

    @commands.group(
        name="playlist",
        description="""Manage playlists""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        usage="Usage",
        aliases=["pl"],
        enabled=True,
        hidden=False,
    )
    async def playlist_manage(self, ctx):
        """Command description"""
        if not ctx.invoked_subcommand:
            embed = discord.Embed(
                title=f"Playlists",
                description=f"""add stuff here later idiot""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color(),
            )
            await ctx.send(embed=embed)

    @playlist_manage.command(
        name="create",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        usage="Usage",
        aliases=["c"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def create_playlist(self, ctx, *, playlist_name: str):
        """Create a playlist"""
        c_status = await self.playlistmanager.create_playlist(
            ctx.author.id, playlist_name
        )
        if c_status == "SUCCESS":
            embed = discord.Embed(
                title=f"Created Playlist",
                description=f"""Created a playlist with the name `{playlist_name}`""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("green"),
            )
            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(
                title=f"Error",
                description=f"""```diff
- {c_status.split(":")[1]} -
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            await ctx.send(embed=embed)

    @playlist_manage.command(
        name="delete",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        usage="Usage",
        aliases=["d"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def delete_playist(self, ctx, *, playlist_name: str):
        """Create a playlist"""
        c_status = await self.playlistmanager.delete_playlist(
            ctx.author.id, playlist_name
        )
        if c_status == "SUCCESS":
            embed = discord.Embed(
                title=f"Delete Playlist",
                description=f"""Deleted playlist `{playlist_name}`""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("green"),
            )
            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(
                title=f"Error",
                description=f"""```diff
- {c_status.split(":")[1]} -
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            await ctx.send(embed=embed)

    @playlist_manage.command(
        name="list",
        description="""Shows a list of all the playlists a user has.""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        usage="Usage",
        aliases=["l"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def playlist_list_cmd(self, ctx):
        """Command description"""

        playlists = await self.playlistmanager.get_playlists(ctx.author.id)

        list_visual = ""
        for count, song in enumerate(list_visual, 1):
            list_visual += f"\n{count}. {song}"

        embed = discord.Embed(
            title=f"Showing {len(playlists)}",
            description=f"""```md
{list_visual}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color(),
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Playlist(bot))
