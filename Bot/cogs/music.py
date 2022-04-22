import aiofiles
import asqlite
import wavelink
from wavelink.ext import spotify
from discord.ext import commands
import discord
import os
from gears import style, util
import datetime


class Player(wavelink.Player):
    """Our custom player with some attributes"""

    def __init__(self, dj: discord.Member):
        """Dj is the person who started this"""
        super().__init__()
        self.dj = dj
        self.queue = wavelink.Queue(max_size=250)

    async def request(self, track):
        """Request a song"""
        if self.queue.is_empty and not self.track:
            await self.play(track)
        elif self.queue.is_full:
            raise QueueFull
        else:
            self.queue.put(track)

    async def skip(self):
        """Skip the currently playing track just an alias"""
        await self.stop()


class MusicException(Exception):
    """Music exception meh"""

    pass


class QueueFull(MusicException):
    """When the queue is full"""

    pass


class NothingPlaying(MusicException):
    """When nothings playing"""

    pass


class PlayerDropdown(discord.ui.Select):
    """
    Shows up to 25 songs in a Select so we can see it
    """

    def __init__(self, ctx, player, songs: list):
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
                    description=f"""{song.author} - Duration: {util.remove_zcs(str(datetime.timedelta(seconds=song.length)))}""",
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
= Duration: {util.remove_zcs(str(datetime.timedelta(seconds=track.length)))} =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("green"),
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

    def __init__(self, ctx, player, songs: list):
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
            color=style.get_color("red"),
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


class Music(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""

    def __init__(self, bot):
        self.bot = bot

    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        if not self.bot.MUSIC_ON:
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
                    client_id=os.getenv("Spotify_ClientID"),
                    client_secret=os.getenv("Spotify_CLIENTSecret"),
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
        try:
            await ctx.guild.change_voice_state(
                channel=ctx.message.author.voice.channel, self_mute=False, self_deaf=True
            )
        except:
            pass
        return player

    @commands.Cog.listener()
    async def on_connect_wavelink(self):
        """On cog load do stuff"""
        await self.connect_nodes()
        async with asqlite.connect("Databases/music.db") as db:
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
        await self.bot.printer.print_load("Recently Played")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node):
        """Event fired when a node has finished connecting."""
        await self.bot.printer.print_connect(f"{node.identifier} is ready.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player, track, reason):
        """On end, check if the queue has another song to play if not disconnect after 5 min"""
        if player.queue.is_empty:
            pass  # add the thing later
        else:
            await player.play(player.queue.get())

    @commands.hybrid_command(
        name="play",
        description="""Description of command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=["p"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def play(self, ctx, *, search):
        """
        Play a song with the given search query.

        If not connected, connect to our voice channel.
        """
        player = await self.get_player(ctx)

        decoded = spotify.decode_url(search)
        if not decoded:
            node = wavelink.NodePool.get_node()
            query = "ytsearch:" + search
            tracks = await node.get_tracks(cls=wavelink.YouTubeTrack, query=query)

            view = PlayerSelector(ctx, player, tracks[:25])

            embed = discord.Embed(
                title=f"{style.get_emoji('regular', 'youtube')} Select a Song to Play",
                description=f"""```asciidoc
= Showing Song Results for: =
[ {search} ]
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("green"),
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
                        title=f"Track Queued",
                        url=track.uri,
                        description=f"""```[ Max Queue Size Reached ]
= Sorry but you only may have 250 songs queued at a time =
```""",
                        timestamp=discord.utils.utcnow(),
                        color=style.get_color("red"),
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
= Duration: {util.remove_zcs(str(datetime.timedelta(seconds=track.length)))} =
```""",
                    timestamp=discord.utils.utcnow(),
                    color=style.get_color("green"),
                )
                embed.set_author(name=track.author)
                embed.set_footer(
                    text=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                )
                await ctx.send(embed=embed)

            elif decoded["type"] == spotify.SpotifySearchType.playlist:
                if ctx.author.id != 360061101477724170:
                    return await ctx.send(
                        "Not supported because I don't wanna fuck the bot"
                    )

                counter = 0
                async for song in spotify.SpotifyTrack.iterator(query=decoded["id"]):
                    if counter == 50:
                        pass
                    else:
                        await player.request(song)
                        counter += 1

                embed = discord.Embed(
                    title=f"{style.get_emoji('regular', 'spotify')} Playing Album",
                    url="https://google.com",
                    description=f"""```asciidoc
[ Album name here ]
= Duration: full duration here please =
```""",
                    timestamp=discord.utils.utcnow(),
                    color=style.get_color("green"),
                )
                embed.set_author(name="Add the author of the album")
                embed.set_footer(
                    text=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                )
                await ctx.send(embed=embed)
                await ctx.send(decoded)

    @commands.hybrid_command(
        name="queue",
        description="""queue viewer""",
        help="""Show what's currently in the players queue!""",
        brief="View Player Queue",
        aliases=["q"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def queue_cmd(self, ctx):
        """Command description"""
        player = await self.get_player(ctx)

        if not player.track:
            nothing_playing = discord.Embed(
                title=f"Nothing Playing",
                description=f"""Nothing's currently playing!""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            return await ctx.send(embed=nothing_playing)

        elif player.queue.is_empty:
            emptyqueue = discord.Embed(
                title=f"Empty Queue",
                description=f"""Nothing's currently queued!""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            return await ctx.send(embed=emptyqueue)

        visual = ""
        total_dur = player.track.length
        for count, track in enumerate(player.queue._queue, 1):
            if isinstance(track, wavelink.PartialTrack):
                visual += f"\n{count}. {track.title} [ N/A ] ( Added from Playlist. )"
            else:
                visual += f"\n{count}. {track.title} [{track.author}] ({util.remove_zcs(str(datetime.timedelta(seconds=track.length)))})"
                total_dur += track.length

        total_dur = util.remove_zcs(str(datetime.timedelta(seconds=total_dur)))

        embed = discord.Embed(
            title=f"Queue - {len(player.queue._queue)} Tracks",
            description=f"""```md
{visual}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("aqua"),
        )
        embed.set_footer(text=f"""Total Duration: {total_dur}""")
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="np",
        description="""Display what's playing rn""",
        help="""Show what's currently being played by Benny""",
        brief="""Now Playing""",
        aliases=["now"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def np_cmd(self, ctx):
        """Showing whats now playing"""
        player = await self.get_player(ctx)

        if not player.is_playing:
            nothing_playing = discord.Embed(
                title=f"Nothing is playing!",
                description=f"""Use `play` to queue a song!""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("aqua"),
            )
            return await ctx.send(embed=nothing_playing)

        else:
            current = player.track

            embed = discord.Embed(
                title=f"Now Playing",
                url=current.uri,
                description=f"""```asciidoc
[ {current.title} ]
= Duration: {util.remove_zcs(str(datetime.timedelta(seconds=current.length)))} =
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color(),
            )
            embed.set_author(name=current.author)

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
    async def skip_cmd(self, ctx):
        """Skip command"""
        player = await self.get_player(ctx)

        try:
            await player.skip()
        except NothingPlaying:
            embed = discord.Embed(
                title=f"Skipped",
                description=f"""blah""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color(),
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="disconnect",
        description="""Disconnect the bot from the channel and remove the player""",
        help="""Disconnect the bot, removing all songs in queue""",
        brief="Disconnect the bot from the voice channel",
        aliases=["dc"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def dc_cmd(self, ctx):
        """Disconnect"""
        player = await self.get_player(ctx)

        await player.disconnect()

    @commands.hybrid_command(
        name="remove",
        description="""remove song from queue""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=["r"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def remove_cmd(self, ctx, *, remove_req: str):
        """
        Will support removing by song name / author soon.
        """
        player = await self.get_player(ctx)

        if remove_req.isnumeric():
            try:
                remove_req = int(remove_req)
                index = remove_req - 1

                song = player.queue._queue[index]

                embed = discord.Embed(
                    title=f"Removed",
                    url=song.uri,
                    description=f"""```asciidoc
[ {song.title} ]
= Duration: {util.remove_zcs(str(datetime.timedelta(seconds=song.length)))} =
```""",
                    timestamp=discord.utils.utcnow(),
                    color=style.get_color("red"),
                )
                embed.set_author(name=song.author)
                await ctx.send(embed=embed)
                del player.queue._queue[index]

            except Exception as e:
                print(e)
                await ctx.send("An error has an occured... uh o")

    @commands.hybrid_command(
        name="musiclogs",
        description="""Display logs""",
        help="""Command displays music logs from lavalink what else""",
        brief="Music Logs",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.is_owner()
    async def musiclogs(self, ctx):
        """Command description"""
        async with aiofiles.open("logs/spring.log") as logs:
            lines = []
            temp = ""
            length = 0
            async for line in logs:
                if length > 4000:
                    lines.append(temp)
                    temp = ""
                else:
                    temp += f"\n{line}"

        for line in lines:
            await ctx.send(line)


async def setup(bot):
    await bot.add_cog(Music(bot))
