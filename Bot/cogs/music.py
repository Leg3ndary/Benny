import asqlite
import datetime
import discord
import discord.utils
import random
import tekore
import wavelink
from discord.ext import commands
from gears import style, util
from gears.music_exceptions import *
from wavelink.ext import spotify


class Player(wavelink.Player):
    """Our custom player with some attributes"""

    def __init__(self, dj: discord.Member) -> None:
        """Dj is the person who started this"""
        super().__init__()
        self.dj = dj
        self.queue = wavelink.Queue(max_size=250)
        self.looping = False

    async def request(self, track) -> None:
        """Request a song"""
        if self.queue.is_empty and not self.track:
            await self.play(track)
        elif self.queue.is_full:
            raise QueueFull("The queue is currently full")
        else:
            self.queue.put(track)

    async def skip(self) -> None:
        """Skip the currently playing track just an alias"""
        if self.queue.is_empty and not self.track:
            raise NothingPlaying("Nothing is currently playing")
        await self.stop()

    async def shuffle(self) -> None:
        """Shuffle the queue"""
        if self.queue.is_empty:
            raise QueueEmpty("The queue is currently empty")
        lq = len(self.queue._queue)

        temp = []
        for i in range(lq):
            temp.append(self.queue._queue[i])

        for i in range(lq):
            self.queue._queue.pop()

        index_list = list(range(lq))
        for i in range(lq):
            ri = random.choice(index_list)
            self.queue._queue.append(temp[ri])
            index_list.pop(index_list.index(ri))

    async def loop(self) -> None:
        """Loop the queue?"""
        if self.queue.is_empty:
            raise QueueEmpty("The queue is currently empty")
        self.looping = not self.looping


class PlayerDropdown(discord.ui.Select):
    """
    Shows up to 25 songs in a Select so we can see it
    """

    def __init__(self, ctx: commands.Context, player, songs: list):
        self.ctx = ctx
        self.player = player
        self.songs = songs
        options = []
        counter = 0
        for song in songs:
            options.append(
                discord.SelectOption(
                    emoji=style.get_emoji("regular", "youtube"),
                    label=song.title,
                    description=f"""{song.author} - Duration: {duration(song.length)}""",
                    value=str(counter),
                )
            )
            counter += 1

        super().__init__(
            placeholder="Select a Song",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"{str(ctx.guild.id)}-{str(ctx.message.id)}=music",
        )

    async def callback(self, interaction: discord.Interaction):
        track = self.songs[int(self.values[0])]

        embed = discord.Embed(
            title=f"Track Queued",
            url=track.uri,
            description=f"""```asciidoc
[ {track.title} ]
= Duration: {duration(track.length)} =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        embed.set_author(name=track.author)
        embed.set_footer(
            text=self.ctx.author.display_name,
            icon_url=self.ctx.author.display_avatar.url,
        )

        await self.player.request(track)
        await interaction.response.edit_message(embed=embed, view=None)
        self.view.stop()


class PlayerSelector(discord.ui.View):
    """Select a song based on what we show from track results."""

    def __init__(self, ctx: commands.Context, player, songs: list):
        self.ctx = ctx
        self.play_embed = None
        super().__init__(timeout=60)

        self.add_item(PlayerDropdown(ctx, player, songs))

    async def interaction_check(self, interaction):
        """If the interaction isn't by the user, return a fail."""
        if interaction.user != self.ctx.author:
            return False
        return True

    async def on_timeout(self):
        """On timeout make this look cool"""
        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title=f"Select a Song to Play",
            description=f"""Timed out""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.RED,
        )
        await self.play_embed.edit(embed=embed, view=self)

    @discord.ui.button(
        emoji=style.get_emoji("regular", "cancel"),
        label="Cancel",
        style=discord.ButtonStyle.danger,
        row=2,
    )
    async def button_callback(self, button, interaction):
        """Delete the message if clicked"""
        await self.play_embed.delete()
        await interaction.response.send_message("Cancelled", ephemeral=True)


def duration(seconds: float) -> str:
    """Return a human readable duration because"""
    return util.remove_zcs(str(datetime.timedelta(seconds=seconds)))


class PlaylistManager:
    """
    Bunch of methods to interact with and update/delete playlists

    Attributes
    ----------
    PLAYLIST_SONG_LIMIT: int
        The max no of songs that a playlist may have
    PLAYLIST_LIMIT: int
        The max no of playlists that a user may have under an ID
    SONG_NAME_LIMIT: int
        The max length of a song name in chars
    """

    def __init__(self, db: asqlite.Connection) -> None:
        """Constructs all the necessary attributes for the PlaylistManager"""
        self.PLAYLIST_SONG_LIMIT = 150
        self.PLAYLIST_LIMIT = 5
        self.SONG_NAME_LIMIT = 50
        self.db = db

    async def create_playlist(self, user_id: str, playlist_name: str) -> None:
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
        None
        """
        async with self.db.execute(
            """SELECT id FROM playlists WHERE id = ?;""", (str(user_id),)
        ) as cursor:
            length = len(await cursor.fetchall())
            if length > self.PLAYLIST_LIMIT:
                raise PlaylistLimitReached("Too many playlists have been created.")

        await self.db.execute(
            """INSERT INTO playlists VALUES(?, ?, 0, "");""",
            (user_id, playlist_name),
        )
        await self.db.commit()

    async def delete_playlist(self, user_id: str, playlist_name: str) -> None:
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
        None
        """
        async with self.db.execute(
            """SELECT id, name FROM playlists WHERE id = ? and name = ?;""",
            (int(user_id), playlist_name),
        ) as cursor:
            if not cursor.fetchall():
                raise PlaylistNotFound(
                    f"Playlist {playlist_name} was not found for deletion."
                )
        await self.db.execute(
            """DELETE FROM playlists WHERE name = ?;""", (playlist_name,)
        )
        await self.db.commit()

    async def add_song(self, user_id: str, playlist_name: str, song: str) -> None:
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
        None
        """
        # Cleaning out commas in which we use as delimiters.
        song = song.replace(",", "")

        if len(song) > self.SONG_NAME_LIMIT:
            return f"ERROR:Please limit the song name to 50 characters ({self.SONG_NAME_LIMIT} currently)"

        async with self.db.execute(
            """SELECT * FROM playlists WHERE id = ? AND name = ?;""",
            (str(user_id), playlist_name),
        ) as cursor:
            if not await cursor.fetch():
                raise PlaylistNotFound(
                    f"Playlist {playlist_name} was not found for song addition."
                )
            else:
                # Songs index is no 3
                data = await cursor.fetch()
                songs_length = data[3].count(", ")
                if (songs_length + 1) > self.PLAYLIST_SONG_LIMIT:
                    raise PlaylistSongLimitReached(
                        f"Playlist {playlist_name} has reached the max amount of songs. ({self.PLAYLIST_SONG_LIMIT})"
                    )
                elif songs_length == 0:
                    prefix = ""
                else:
                    prefix = ", "
        await self.db.execute(
            f"""INSERT INTO playlists VALUES(?, ?, ?, ?);""",
            (data[0], data[1], data[2], data[4].append(prefix + song)),
        )
        await self.db.commit()

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

        async with self.db.execute(
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
        await self.db.execute(
            f"""DELETE FROM playlists WHERE id = ?, ?, ?, ?);""",
            (data[0], data[1], data[2], data[4].append(prefix)),
        )
        await self.db.commit()
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
        async with self.db.execute(
            """SELECT * FROM playlists WHERE id = ?;""", (str(user_id),)
        ) as cursor:
            playlists = await cursor.fetchall()
            return playlists


class Music(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        app_token = tekore.request_client_token(
            bot.config.get("Spotify").get("ID"), bot.config.get("Spotify").get("Secret")
        )
        self.spotify = tekore.Spotify(
            token=app_token, asynchronous=True, max_limits_on=True
        )

    async def cog_load(self):
        """Load up playlist related stuff"""
        self.playlist_db = await asqlite.connect("Databases/music.db")
        await self.playlist_db.execute(
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
        self.playlistmanager = PlaylistManager(self.playlist_db)
        await self.bot.printer.p_load("Playlist")

    async def connect_nodes(self):
        """Connect to our wavelink nodes."""
        if not self.bot.MUSIC_ENABLED:
            return

        # Making sure cog loads and unloads don't stop this
        if hasattr(self.bot, "wavelink"):
            self.wavelink = self.bot.wavelink
        else:
            self.bot.wavelink = await wavelink.NodePool.create_node(
                bot=self.bot,
                host="localhost",
                port=2333,
                region="na",
                password="BennyBotRoot",
                identifier="Benny1",
                spotify_client=spotify.SpotifyClient(
                    client_id=self.bot.config.get("Spotify").get("ID"),
                    client_secret=self.bot.config.get("Spotify").get("Secret"),
                ),
            )
            self.wavelink = self.bot.wavelink

    async def get_player(self, ctx) -> wavelink.Player:
        """Create a player and connect cls"""
        if not ctx.voice_client:
            player: wavelink.Player = await ctx.author.voice.channel.connect(
                cls=Player(dj=ctx.author)
            )
        else:
            player: wavelink.Player = ctx.voice_client

            await ctx.guild.change_voice_state(
                channel=ctx.message.author.voice.channel,
                self_mute=False,
                self_deaf=True,
            )

        return player

    @commands.Cog.listener()
    async def on_connect_wavelink(self):
        """On cog load do stuff"""
        await self.connect_nodes()
        self.musicDB = await asqlite.connect("Databases/music.db")
        async with self.musicDB as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS recently_played (
                    id TEXT NOT NULL
                            PRIMARY KEY,
                    s1 TEXT,
                    s2 TEXT,
                    s3 TEXT,
                    s4 TEXT,
                    s5 TEXT,
                    s6 TEXT,
                    s7 TEXT,
                    s8 TEXT,
                    s9 TEXT,
                    s10 TEXT,
                    s11 TEXT,
                    s12 TEXT,
                    s13 TEXT,
                    s14 TEXT,
                    s15 TEXT,
                    s16 TEXT,
                    s17 TEXT,
                    s18 TEXT,
                    s19 TEXT,
                    s20 TEXT,
                    s21 TEXT,
                    s22 TEXT,
                    s23 TEXT,
                    s24 TEXT,
                    s25 TEXT
                );
                """
            )
        await self.bot.printer.p_load("Recently Played")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node):
        """Event fired when a node has finished connecting."""
        await self.bot.printer.p_connect(f"{node.identifier} is ready.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player, track, reason):
        """On end, check if the queue has another song to play if not disconnect after 5 min"""
        if player.queue.is_empty:
            self.bot.loop.create_task()
        else:
            if player.looping:
                await player.request(track)
            await player.play(player.queue.get())

    @commands.hybrid_command(
        name="play",
        description="""Play a song/Queue another song""",
        help="""Play a song or request in the queue""",
        brief="Play a song",
        aliases=["p"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def play(self, ctx: commands.Context, *, song: str):
        """
        Play a song with the given search query.

        If not connected, connect to our voice channel.
        """
        player = await self.get_player(ctx)

        '''
        async with self.musicDB as db:
            is_created = await db.execute(
                """SELECT id FROM recently_played WHERE id = ?;""",
                (str(ctx.author.id), )
            )
            if not is_created:
                await db.execute(
                    f"""INSERT INTO recently_played VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                    (str(ctx.author.id), None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None),
                )
                await self.db.commit()
        '''

        decoded = spotify.decode_url(song)
        if not decoded:
            node = wavelink.NodePool.get_node()
            query = "ytsearch:" + song
            tracks = await node.get_tracks(cls=wavelink.YouTubeTrack, query=query)

            view = PlayerSelector(ctx, player, tracks[:25])

            embed = discord.Embed(
                title=f"{style.get_emoji('regular', 'youtube')} Select a Song to Play",
                description=f"""```asciidoc
= Showing Song Results for: =
[ {song} ]
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREEN,
            )
            view.play_embed = await ctx.send(embed=embed, view=view)

        else:
            if decoded["type"] == spotify.SpotifySearchType.track:
                track = await spotify.SpotifyTrack.search(
                    query=decoded["id"], return_first=True
                )

                if player.queue.is_empty and not player.track:
                    await player.request(track)
                elif player.queue.is_full:
                    embed = discord.Embed(
                        title=f"Max Queue Size Reached",
                        url=track.uri,
                        description=f"""Sorry but you only may have 250 songs queued at a time""",
                        timestamp=discord.utils.utcnow(),
                        color=style.Color.RED,
                    )
                    embed.set_author(name=track.author)
                    embed.set_footer(
                        text=self.ctx.author.display_name,
                        icon_url=self.ctx.author.display_avatar.url,
                    )
                    return await ctx.send(embed)
                else:
                    player.queue.put(track)

                embed = discord.Embed(
                    title=f"{style.get_emoji('regular', 'spotify')} Playing Track",
                    url=track.uri,
                    description=f"""```asciidoc
[ {track.title} ]
= Duration: {duration(track.length)} =
```""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.GREEN,
                )
                embed.set_author(name=track.author)
                embed.set_footer(
                    text=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                )
                await ctx.send(embed=embed)

            elif decoded["type"] == spotify.SpotifySearchType.playlist:
                length = int(
                    (await self.spotify.playlist(decoded["id"], fields="tracks(total)"))
                    .get("tracks")
                    .get("total")
                )

                if length >= 100:
                    embed = discord.Embed(
                        title=f"Playlist Song Limit Reached",
                        description=f"""You may only add up to 100 songs through spotify playlists at this time""",
                        timestamp=discord.utils.utcnow(),
                        color=style.Color.RED,
                    )
                    return await ctx.send(embed=embed)

                playlist = await self.spotify.playlist(decoded["id"])

                if playlist.owner:
                    author = playlist.owner.display_name
                else:
                    author = "Featured Playlist"

                embed = discord.Embed(
                    title=f"{style.get_emoji('regular', 'spotify')} Queueing {playlist.name}",
                    description=f"""```asciidoc
[ Adding {length} Songs ]
= Duration: Calculating =
```""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.GREY,
                )
                embed.set_author(name=author)
                embed.set_footer(
                    text=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                )
                msg = await ctx.send(embed=embed)

                total_dur = 0
                async for song in spotify.SpotifyTrack.iterator(query=decoded["id"]):
                    await player.request(song)
                    total_dur += song.length

                finished = discord.Embed(
                    title=f"{style.get_emoji('regular', 'spotify')} Playing {playlist.name}",
                    url=playlist.href,
                    description=f"""```asciidoc
[ Added {length} Songs ]
= Duration: {duration(total_dur)} =
```""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.GREEN,
                )
                embed.set_author(name=author)
                embed.set_footer(
                    text=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                )
                await msg.edit(embed=finished)

    @commands.hybrid_command(
        name="queue",
        description="""View the current queue""",
        help="""Show what's currently in the players queue!""",
        brief="View Player Queue",
        aliases=["q"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def queue_cmd(self, ctx: commands.Context) -> None:
        """Command description"""
        player = await self.get_player(ctx)

        if not player.track:
            nothing_playing = discord.Embed(
                title=f"Nothing Playing",
                description=f"""Nothing's currently playing!""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            return await ctx.send(embed=nothing_playing)

        elif player.queue.is_empty:
            emptyqueue = discord.Embed(
                title=f"Empty Queue",
                description=f"""Nothing's currently queued!""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            return await ctx.send(embed=emptyqueue)

        visual = ""
        total_dur = player.track.length
        for count, track in enumerate(player.queue._queue, 1):
            if isinstance(track, wavelink.PartialTrack):
                visual += f"\n{count}. {track.title} [ N/A ] ( Added from Playlist. )"
            else:
                visual += f"\n{count}. {track.title} [{track.author}] ({duration(track.length)})"
                total_dur += track.length

        total_dur = duration(total_dur)

        embed = discord.Embed(
            title=f"Queue - {len(player.queue._queue)} Tracks",
            description=f"""```md
{visual}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        embed.set_footer(text=f"""Total Duration: {total_dur}""")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="now",
        description="""Show what songs currently being played""",
        help="""Show whats currently being played by Benny""",
        brief="""Now Playing""",
        aliases=["nowplaying", "np"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def nowplaying_cmd(self, ctx: commands.Context) -> None:
        """
        Showing whats now playing
        """
        player = await self.get_player(ctx)

        if not player.is_playing:
            nothing_playing = discord.Embed(
                title=f"Nothing is playing!",
                description=f"""Use the play command to queue a song!""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.AQUA,
            )
            return await ctx.send(embed=nothing_playing)

        else:
            current = player.track

            embed = discord.Embed(
                title=f"Now Playing",
                url=current.uri,
                description=f"""```asciidoc
[ {current.title} ]
= Duration: {duration(current.length)} =
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.random(),
            )
            embed.set_author(name=current.author)
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="skip",
        description="""Skip command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=["s"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 5.0, commands.BucketType.user)
    async def skip_cmd(self, ctx: commands.Context) -> None:
        """Skip command"""
        player = await self.get_player(ctx)

        try:
            current = player.track
            await player.skip()
            embed = discord.Embed(
                title=f"Skipped",
                url=current.uri,
                description=f"""```asciidoc
[ {current.title} ]
= Duration: {duration(current.length)} =
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.ORANGE,
            )
            embed.set_author(name=current.author)
            await ctx.send(embed=embed)

        except NothingPlaying as e:
            embed = discord.Embed(
                title=f"Error",
                description=f"""{e}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="disconnect",
        description="""Disconnect the bot from the voice channel""",
        help="""Disconnect the bot, removing all songs in queue""",
        brief="Disconnect the bot from the voice channel",
        aliases=["dc"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def dc_cmd(self, ctx: commands.Context) -> None:
        """Disconnect"""
        player = await self.get_player(ctx)

        await player.disconnect()

    @commands.hybrid_command(
        name="remove",
        description="""Remove a song from the Queue""",
        help="""Remove a song from a certain index from the queue""",
        brief="Remove a song from the queue",
        aliases=["r"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def remove_cmd(self, ctx: commands.Context, *, number: str):
        """
        Will support removing by song name / author soon.
        """
        player = await self.get_player(ctx)

        if number.isnumeric():
            try:
                number = int(number)
                index = number - 1

                song = player.queue._queue[index]

                embed = discord.Embed(
                    title=f"Removed",
                    url=song.uri,
                    description=f"""```asciidoc
[ {song.title} ]
= Duration: {duration(song.length)} =
```""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.RED,
                )
                embed.set_author(name=song.author)
                await ctx.send(embed=embed)
                del player.queue._queue[index]

            except Exception as e:
                print(e)
                await ctx.send("An error has an occured... uh o")

    @commands.hybrid_command(
        name="shuffle",
        description="""Shuffle the queue""",
        help="""Shuffle the entire queue""",
        brief="Shuffle the queue",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def shuffle_cmd(self, ctx: commands.Context) -> None:
        """Shuffle the queue"""
        player = await self.get_player(ctx)

        try:
            current = player.track
            await player.shuffle()
            embed = discord.Embed(
                title=f"{style.get_emoji('regular', 'shuffle')} Shuffling",
                url=current.uri,
                description=f"""Shuffled {len(player.queue._queue)} songs""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.YELLOW,
            )
            await ctx.send(embed=embed)

        except QueueEmpty as e:
            embed = discord.Embed(
                title=f"Error",
                description=f"""{e}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="loop",
        description="""Loop/Unloop the queue""",
        help="""Either loop or unloop the queue""",
        brief="Loop/Unloop the queue",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def loop_cmd(self, ctx: commands.Context) -> None:
        """Looping command noice"""
        player = await self.get_player(ctx)

        try:
            current = player.track
            await player.loop()
            if player.loop:
                vis = "Loop"
            else:
                vis = "Unloop"

            embed = discord.Embed(
                title=f"{style.get_emoji('regular', 'loop')} {vis}ing",
                url=current.uri,
                description=f"""{vis}ed the queue""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.AQUA,
            )
            await ctx.send(embed=embed)

        except QueueEmpty as e:
            embed = discord.Embed(
                title=f"Error",
                description=f"""{e}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await ctx.send(embed=embed)

    @commands.group(
        name="playlist",
        description="""Manage playlists""",
        help="""Take a look at all of your playlists""",
        brief="""Short help text""",
        aliases=["pl"],
        enabled=True,
        hidden=False,
    )
    async def playlist_manage(self, ctx: commands.Context) -> None:
        """Command description"""
        if not ctx.invoked_subcommand:
            embed = discord.Embed(
                title=f"Playlists",
                description=f"""add stuff here later idiot""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.random(),
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
    async def create_playlist(self, ctx: commands.Context, *, playlist_name: str):
        """Create a playlist"""
        try:
            c_status = await self.playlistmanager.create_playlist(
                ctx.author.id, playlist_name
            )
            embed = discord.Embed(
                title=f"Created Playlist",
                description=f"""Created a playlist with the name `{playlist_name}`""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREEN,
            )
            await ctx.send(embed=embed)

        except PlaylistLimitReached as e:
            embed = discord.Embed(
                title=f"Error",
                description=f"""```diff
- {e} -
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
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
    async def delete_playist(self, ctx: commands.Context, *, playlist_name: str):
        """Create a playlist"""
        try:
            c_status = await self.playlistmanager.delete_playlist(
                ctx.author.id, playlist_name
            )
            embed = discord.Embed(
                title=f"Delete Playlist",
                description=f"""Deleted playlist `{playlist_name}`""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREEN,
            )
            await ctx.send(embed=embed)

        except PlaylistNotFound as e:
            embed = discord.Embed(
                title=f"Error",
                description=f"""```diff
- {e} -
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
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
    async def playlist_list_cmd(self, ctx: commands.Context) -> None:
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
            color=style.Color.random(),
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))
