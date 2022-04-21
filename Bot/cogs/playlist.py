import asqlite
import discord
import discord.utils
from discord.ext import commands
from gears import style


class PlaylistException(Exception):
    """
    Raised when a playlist related function has an error
    """
    
    pass


class PlaylistLimitReached(PlaylistException):
    """
    Raised when the max amount of playlists has been made
    """

    pass

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

    async def create_playlist(self, user_id: str, playlist_name: str) -> str:
        """
        Create a playlist in our database

        Parameters
        ----------
        user_id: str
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
        async with asqlite.connect("Databases/music.db") as db:
            async with db.execute(
                """SELECT id FROM playlists WHERE id = ?;""", (str(user_id),)
            ) as cursor:
                length = len(await cursor.fetchall())
                if length > self.PLAYLIST_LIMIT:
                    raise PlaylistLimitReached()

            await db.execute(
                """INSERT INTO playlists VALUES(?, ?, 0, "");""",
                (user_id, playlist_name),
            )
            await db.commit()
            return "SUCCESS"

    async def delete_playlist(self, user_id: str, playlist_name: str) -> str:
        """
        Delete a playlist in our database

        Parameters
        ----------
        user_id: str
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
        async with asqlite.connect("Databases/music.db") as db:
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

    async def add_song(self, user_id: str, playlist_name: str, song: str) -> str:
        """
        Add a song to a playlist by ID

        Parameters
        ----------
        user_id: str
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

        async with asqlite.connect("Databases/music.db") as db:
            async with db.execute(
                """SELECT * FROM playlists WHERE id = ? AND name = ?;""",
                (str(user_id), playlist_name),
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

    async def delete_song(self, user_id: str, playlist_name: str, song_index) -> str:
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

        async with asqlite.connect("Databases/music.db") as db:
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

    async def get_playlists(self, user_id: str) -> list:
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
        async with asqlite.connect("Databases/music.db") as db:
            async with db.execute(
                """SELECT * FROM playlists WHERE id = ?;""", (str(user_id),)
            ) as cursor:
                playlists = await cursor.fetchall()
                return playlists


class Playlist(commands.Cog):
    """Manage and view playlists which you can also use to interact and listen too"""

    def __init__(self, bot):
        self.bot = bot
        self.playlistmanager = PlaylistManager()

    async def cog_load(self):
        """Load up playlist related stuff"""
        async with asqlite.connect("Databases/music.db") as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS playlists (
                    id    TEXT    NOT NULL
                                PRIMARY KEY,
                    name  TEXT    NOT NULL,
                    plays INTEGER NOT NULL,
                    songs TEXT
                );
                """
            )
        await self.bot.printer.print_load("Playlist")

    @commands.group(
        name="playlist",
        description="""Manage playlists""",
        help="""Take a look at all of your playlists""",
        brief="""Short help text""",
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


async def setup(bot):
    await bot.add_cog(Playlist(bot))
