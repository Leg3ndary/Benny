import asqlite
import asyncio
import discord
import lavalink
import math
import os
import re
import tekore
from discord.ext import commands
from gears import cviews, style, util


url_rx = re.compile(r"https?://(?:www\.)?.+")


def get_size(bytes, suffix="B"):
    """Return the correct data from bytes"""
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


class LavalinkVoiceClient(discord.VoiceClient):
    """
    LavalinkVoiceClient that we use to stream music to a discord voice channel
    """

    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        """Initialize a LavalinkVoiceClient if we haven't already..."""
        self.client = client
        self.channel = channel
        # Check if a client already exists
        if hasattr(self.client, "lavalink"):
            self.lavalink = self.client.lavalink
        else:
            self.client.lavalink = lavalink.Client(889672871620780082)
            self.client.lavalink.add_node(
                "localhost", 2333, "BennyBotRoot", "na", "default-node"
            )
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        """The data needs to be transformed before being handed down to voice_update_handler"""
        lavalink_data = {"t": "VOICE_SERVER_UPDATE", "d": data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        """The data needs to be transformed before being handed down to voice_update_handler"""
        lavalink_data = {"t": "VOICE_STATE_UPDATE", "d": data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool) -> None:
        """
        Connect the client to the voice channel and create a player_manager
        if it doesn't exist yet.
        """
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel)

    async def disconnect(self, *, force: bool) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        # Don't disconnect if we aren't even connected
        if not force and not player.is_connected:
            return

        # None means disconnect
        await self.channel.guild.change_voice_state(channel=None)

        player.set_repeat(False)
        player.set_shuffle(False)
        player.queue.clear()
        player.channel_id = None
        await player.stop()
        self.cleanup()


class SpotifyClient:
    """Convert music into song titles so we can search them accurately"""

    def __init__(self, client):
        """Init with a url that we can use"""
        self.client = client
        spotify_token = tekore.request_client_token(
            os.getenv("Spotify_ClientID"), os.getenv("Spotify_CLIENTSecret")
        )
        self.client.spotify = tekore.Spotify(spotify_token, asynchronous=True)
        self.playlist_limit = 100

    async def search_spotify(self, player, ctx, args: str) -> None:
        """
        Search a spotify link and return in the format `title artist`
        Parameters
        ------------
        Player:
            The actual player
        Ctx:
            Command context
        Args:
            The search

        Returns
        -------
        None
        """
        # We already verified this is legit
        from_url = tekore.from_url(args)

        if from_url[0] == "track":
            track = await self.client.spotify.track(from_url[1])
            title = track.name
            artist = track.artists[0].name

            query = f"ytsearch:{title} {artist}"
            results = await player.node.get_tracks(query)

            if not results or not results["tracks"]:
                nothing_found = discord.Embed(
                    title=f"Error",
                    description=f"""Sorry, but nothing was found for the search `{query}`""",
                    timestamp=discord.utils.utcnow(),
                    color=style.get_color("red"),
                )
                return await ctx.send(embed=nothing_found, delete_after=10)

            ps_view = cviews.PlayerSelector(ctx, player, results["tracks"][:25])

            embed = discord.Embed(
                title=f"{style.get_emoji('regular', 'spotify')} Select a Song to Play",
                description=f"""```asciidoc
= Showing Song Results for: =
[ {args} ]
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("green"),
            )
            ps_view.play_embed = await ctx.send(embed=embed, view=ps_view)

        elif from_url[0] == "playlist":
            # Not done
            return ctx.send("Sorry playlists currently aren't supported")
            playlistId = tekore.from_url(args)
            try:
                playlist = await self.bot.spotify.playlist(playlistId[1])
            except:
                await ctx.send(
                    f"{self.bot.emojiList.false} {ctx.author.mention} The Spotify playlist is invalid!"
                )
                return None
            trackLinks = []

            if self.playlistLimit != 0 and playlist.tracks.total > self.playlistLimit:
                playlistTL = discord.Embed(
                    title=f"Error",
                    description=f"""The playlist is too large!""",
                    timestamp=discord.utils.utcnow(),
                    color=style.get_color("red"),
                )
                return await ctx.send(embed=playlistTL, delete_after=10)

            await ctx.send(
                f"{self.bot.emojiList.spotifyLogo} Loading... (This process can take several seconds)",
                delete_after=60,
            )
            for i in playlist.tracks.items:
                title = i.track.name
                artist = i.track.artists[0].name
                # Search on youtube
                track = await self.bot.wavelink.get_tracks(f"ytsearch:{title} {artist}")
                if track is None:
                    await ctx.send(
                        f"{self.bot.emojiList.false} {ctx.author.mention} No song found to : `{title} - {artist}` !"
                    )
                else:
                    trackLinks.append(track[0])
            if not trackLinks:  # if len(trackLinks) == 0:
                return None
            return trackLinks

        else:
            not_supported = discord.Embed(
                title=f"Error",
                description=f"""Sorry but currently type `{from_url[0]}` is not supported""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            await ctx.send(embed=not_supported)


class Music(commands.Cog):
    """The music cog that plays all of our music"""

    def __init__(self, client):
        self.client = client
        self.client.expiring_players = []
        self.search_prefix = client.config.get("Lavalink").get("Search")
        # When reloaded, doesn't terminate connection with client
        if not hasattr(client, "lavalink"):
            client.lavalink = lavalink.Client(889672871620780082)
            # Host, Port, Password, Region, Name
            client.lavalink.add_node(
                "localhost", 2333, "BennyBotRoot", "na", "default-node"
            )

        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        """
        Cog unload handler. This removes any event hooks that were registered
        """
        self.client.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        """
        A guild only check
        """
        guild_check = ctx.guild is not None
        if guild_check:
            await self.ensure_voice(ctx)
        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            embed = discord.Embed(
                title=f"Error",
                description=f"""```diff
- {error.original} -
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            await ctx.send(embed=embed)
            print(error)

    async def ensure_voice(self, ctx):
        """
        Either creates or returns a player if one exists, to ensure we can actually have
        a player at the ready.

        This check ensures that the client and command author are in the same voicechannel.
        """
        player = self.client.lavalink.player_manager.create(
            ctx.guild.id, endpoint=str(ctx.guild.region)
        )

        # Commands that require the client to join a voicechannel (i.e. initiating playback).
        should_connect = ctx.command.name in ("play", "loop", "remove")

        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandInvokeError("Join a voicechannel first.")

        if not player.is_connected:
            if not should_connect:
                raise commands.CommandInvokeError("Not connected.")

            permissions = ctx.author.voice.channel.permissions_for(ctx.me)

            if (
                not permissions.connect or not permissions.speak
            ):  # Check user limit too?
                raise commands.CommandInvokeError(
                    "I need the CONNECT and SPEAK permissions for this to work."
                )

            player.store("channel", ctx.channel.id)

            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                raise commands.CommandInvokeError("You need to be in my voicechannel.")

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            # We check if its already in our expired things, then if not then we add it and start the dispatch
            guild_id = int(event.player.guild_id)

            if guild_id in self.client.expiring_players:
                pass
            else:
                self.client.expiring_players.append(guild_id)
                self.client.dispatch("expire_player", guild_id)

    @commands.Cog.listener()
    async def on_load_spotify(self):
        """Load our spotify client"""
        self.spotifyclient = SpotifyClient(self.client)
        await self.client.printer.print_connect("Tekore Spotify")

    @commands.Cog.listener()
    async def on_expire_player(self, guild_id: int):
        """Expire players when we dispatch it, we check after 180 seconds"""
        await asyncio.sleep(180.0)
        if guild_id in self.client.expiring_players:
            guild = self.client.get_guild(guild_id)
            await guild.voice_client.disconnect(force=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """When everyones left a voice channel, also leave in 3 minutes, also remove from expiring_players if someone rejoins"""
        player = self.client.lavalink.player_manager.get(member.guild.id)
        try:
            if (
                before.channel.id == int(player.channel_id)
                and not after.channel
                and len(before.channel.members) == 0
            ):
                if int(member.guild.id) in self.client.expiring_players:
                    pass
                else:
                    self.client.expiring_players.append(int(member.guild.id))
                    self.client.dispatch("expire_player", int(member.guild.id))
            elif int(after.channel.id) == int(player.channel_id):
                try:
                    self.client.expiring_players.remove(int(member.guild.id))
                except:
                    pass
        except AttributeError:
            pass
        except TypeError:
            pass

    @commands.command(
        name="play",
        description="""Queue up a song""",
        help="""Play a song!
        You can use regular words or a spotify link!""",
        brief="Play songs",
        aliases=["p"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 1.5, commands.BucketType.user)
    async def play_cmd(self, ctx, *, song: str):
        """Searches and plays a song from a given query."""
        if ctx.guild.id in self.client.expiring_players:
            self.client.expiring_players.remove(ctx.guild.id)

        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        query = song.strip("<>")

        try:
            if not url_rx.match(query):
                query = f"{self.search_prefix}:{query}"

            elif tekore.from_url(query):
                await self.spotifyclient.search_spotify(player, ctx, query)
                return
        except tekore.ConversionError:
            pass

        results = await player.node.get_tracks(query)

        # Results could be None if Lavalink returns an invalid response results["tracks"] could be an empty array if the query yielded no tracks
        if not results or not results["tracks"]:
            nothing_found = discord.Embed(
                title=f"Error",
                description=f"""Sorry, but nothing was found for the search `{query}`""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            return await ctx.send(embed=nothing_found, delete_after=10)

        embed = discord.Embed(color=style.get_color())

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        if results["loadType"] == "PLAYLIST_LOADED":
            return await ctx.send(
                "Sorry, currently regular playlists aren't supported."
            )
            tracks = results["tracks"]

            for track in tracks:
                # Add all of the tracks from the playlist to the queue.
                player.add(requester=ctx.author.id, track=track)

            embed.title = "Playlist Queued!"
            embed.description = (
                f"""{results["playlistInfo"]["name"]} - {len(tracks)} tracks"""
            )

            await ctx.send(embed=embed)

        else:
            ps_view = cviews.PlayerSelector(ctx, player, results["tracks"][:25])
            embed = discord.Embed(
                title=f"Select a Song to Play",
                description=f"""```asciidoc
= Showing Song Results for: =
[ {song} ]
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("grey"),
            )
            ps_view.play_embed = await ctx.send(embed=embed, view=ps_view)

    @commands.command(
        name="remove",
        description="""Remove a song from the queue""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        aliases=["r"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def remove_cmd(self, ctx, index: int):
        """Remove command"""
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if not player.queue:
            nothing_playing = discord.Embed(
                title=f"Nothing is queued!",
                description=f"""Use `play` to queue a song!""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("aqua"),
            )
            return await ctx.send(embed=nothing_playing)

        track = player.queue[index - 1]

        del player.queue[index - 1]

        embed = discord.Embed(
            title=f"Removed {index}.",
            url=track.uri,
            description=f"""```asciidoc
[ {track.title} ]
= Duration: {util.remove_zcs(lavalink.format_time(track.duration))} =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("red"),
        )
        embed.set_author(name=track.author)

        requester = self.client.get_user(track.requester)

        if not requester:
            requester = await self.client.fetch_user(track.requester)

        embed.set_footer(
            text=requester.display_name, icon_url=requester.display_avatar.url
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="clear",
        description="""clear the queue""",
        help="""Clear the entire queue, requires confirmation""",
        brief="Clear the queue",
        aliases=[],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def clear_command(self, ctx):
        """Clear the queue"""
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        
        if not player.is_playing:
            nothing_playing = discord.Embed(
                title=f"Nothing is playing!",
                description=f"""Use `play` to queue a song!""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("aqua"),
            )
            return await ctx.send(embed=nothing_playing)
        queue = player.queue
        if not queue:
            embed = discord.Embed(
                title=f"Nothing's been Queued!",
                description=f"""Use the play command to queue more songs!""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("aqua"),
            )
            return await ctx.send(embed=embed)
        else:
            songs = len(queue)
            
            view = cviews.QueueClear(ctx, queue)
            embed = discord.Embed(
                title=f"Confirm",
                description=f"""Are you sure you want to clear the queue?
                This will remove **{songs}** songs.""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("grey")
            )
            embed.set_footer(
                text="This action is irreversible"
            )
            view.embed = await ctx.send(embed=embed, view=view)


    @commands.command(
        name="skip",
        description="""skip the song""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        aliases=["s"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 3.0, commands.BucketType.user)
    async def skip_cmd(self, ctx):
        """Skip the song and move onto the next one"""
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        
        if not player.is_playing:
            nothing_playing = discord.Embed(
                title=f"Nothing is playing!",
                description=f"""Use `play` to queue a song!""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("aqua"),
            )
            return await ctx.send(embed=nothing_playing)

        else:
            current = player.current

            embed = discord.Embed(
                title=f"Skipping",
                url=current.uri,
                description=f"""```asciidoc
[ {current.title} ]
= Duration: {util.remove_zcs(lavalink.format_time(current.duration))} =
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color(),
            )
            embed.set_author(name=current.author)

            requester = self.client.get_user(current.requester)

            if not requester:
                requester = await self.client.fetch_user(current.requester)

            embed.set_footer(
                text=requester.display_name, icon_url=requester.display_avatar.url
            )
            await player.skip()
            await ctx.send(embed=embed)

    @commands.command(
        name="loop",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def loop_cmd(self, ctx):
        """Loop the song or unloop it... The bot will tell you"""
        player = self.client.lavalink.player_manager.get(ctx.guild.id)

        loop = player.repeat

        if not loop:
            player.set_repeat(not loop)
            title = "Looping"
            description = "Looping the current queue"
        elif loop:
            player.set_repeat(not loop)
            title = "Unlooping"
            description = "Unlooping the current queue"

        view = cviews.LoopButton(False, player.repeat, player)

        embed = discord.Embed(
            title=f"""{style.get_emoji("regular", "loop")} {title}""",
            description=f"""{description}""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("aqua"),
        )
        view.bctx = await ctx.send(embed=embed, view=view)

    @commands.command(
        name="queue",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        aliases=["q"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def queue_cmd(self, ctx):
        """Show the command queue"""
        player = self.client.lavalink.player_manager.get(ctx.guild.id)

        queue = player.queue

        if not queue:
            # Queue is empty
            embed = discord.Embed(
                title=f"Nothing's been Queued!",
                description=f"""Use the play command to queue more songs!""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("aqua"),
            )
            return await ctx.send(embed=embed)

        queue_visual = ""

        total_duration = 0
        total_duration += player.current.duration

        for count, track in enumerate(queue, 1):
            queue_visual = f"{queue_visual}\n{count}. {track.title} [{track.author}] ({util.remove_zcs(lavalink.format_time(track.duration))})"
            total_duration += track.duration

        embed = discord.Embed(
            title=f"Queue - {len(queue)} Tracks",
            description=f"""```md
{queue_visual}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("green"),
        )
        if player.repeat:
            lemoji = style.get_emoji("regular", "check")
        else:
            lemoji = style.get_emoji("regular", "cancel")
        if player.shuffle:
            semoji = style.get_emoji("regular", "check")
        else:
            semoji = style.get_emoji("regular", "cancel")
        embed.add_field(
            name="Other Info",
            value=f"""Loop {lemoji}
            Shuffle {semoji}""",
            inline=False,
        )
        embed.set_footer(
            text=f"""Total Duration: {util.remove_zcs(lavalink.format_time(total_duration))}"""
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="np",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        aliases=["now"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def np_cmd(self, ctx):
        """Showing whats now playing"""
        player = self.client.lavalink.player_manager.get(ctx.guild.id)

        if not player.is_playing:
            nothing_playing = discord.Embed(
                title=f"Nothing is playing!",
                description=f"""Use `play` to queue a song!""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("aqua"),
            )
            return await ctx.send(embed=nothing_playing)

        else:
            current = player.current

            embed = discord.Embed(
                title=f"Now Playing",
                url=current.uri,
                description=f"""```asciidoc
[ {current.title} ]
= Duration: {util.remove_zcs(lavalink.format_time(current.duration))} =
```""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color(),
            )
            embed.set_author(name=current.author)

            requester = self.client.get_user(current.requester)

            if not requester:
                requester = await self.client.fetch_user(current.requester)

            embed.set_footer(
                text=requester.display_name, icon_url=requester.display_avatar.url
            )
            await ctx.send(embed=embed)

    @commands.command(
        name="disconnect",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        aliases=["dc"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def disconnect_cmd(self, ctx):
        """Disconnects the player from the voice channel and clears its queue."""
        player = self.client.lavalink.player_manager.get(ctx.guild.id)

        player.set_repeat(False)
        player.set_shuffle(False)

        if not player.is_connected:
            nc = discord.Embed(
                title=f"Error",
                description=f"""Not connected, join a voice channel and use the `play` command to get started!""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            return await ctx.send(embed=nc, delete_after=10)

        if not ctx.author.voice or (
            player.is_connected
            and ctx.author.voice.channel.id != int(player.channel_id)
        ):
            embed = discord.Embed(
                title=f"Error",
                description=f""""You're not in my voicechannel!""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            return await ctx.send(embed=embed, delete_after=10)

        player.queue.clear()
        player.channel_id = None
        await player.stop()

        await ctx.voice_client.disconnect(force=True)
        dc = discord.Embed(
            title=f"Disconnected",
            description=f"""Disconnected successfully.""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("green"),
        )
        await ctx.send(embed=dc)

    @commands.command(
        name="musicstats",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        aliases=[],
        enabled=True,
        hidden=True,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def musicstats_cmd(self, ctx):
        """Show music stats"""
        player = self.client.lavalink.player_manager.get(ctx.guild.id)

        stats = player.node.stats
        embed = discord.Embed(
            title=f"Lavalink Statistics",
            description=f"""```yaml
Uptime: {util.remove_zcs(lavalink.format_time(stats.uptime))}
Players: {stats.players}

Memory Free: {get_size(stats.memory_free)}
Memory Used: {get_size(stats.memory_used)}
Memory Allocated: {get_size(stats.memory_allocated)}
Memory Reservable: {get_size(stats.memory_reservable)}

CPU Cores: {stats.cpu_cores}
Total System Load: {math.trunc(stats.system_load * 10000) / 100}%
Lavalink System Load: {stats.lavalink_load}

Frames Sent to Discord: {stats.frames_sent}
Empty Frames: {stats.frames_nulled}
Missing Frames: {stats.frames_deficit}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color(),
        )
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Music(client))
