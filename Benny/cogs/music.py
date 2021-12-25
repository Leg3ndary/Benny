import discord
import lavalink
import os
import re
import tekore
from discord.ext import commands
from gears.msg_views import LoopButton, PlayerSelector
from gears.style import c_get_color, c_get_emoji


url_rx = re.compile(r"https?://(?:www\.)?.+")


async def send_play_command(ctx, player):
    """Send the play command with relevant information"""



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

        self.client

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
        # Make sure there's a player_manager when creating a new voice_client
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel)

    async def disconnect(self, *, force: bool) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        # no need to disconnect if we are not connected
        if not force and not player.is_connected:
            return

        # None means disconnect
        await self.channel.guild.change_voice_state(channel=None)

        # update the channel_id of the player to None
        # this must be done because the on_voice_state_update that
        # would set channel_id to None doesn't get dispatched after the
        # disconnect
        player.channel_id = None
        self.cleanup()


class SpotifyClient:
    """Convert music into song titles so we can search them accurately"""

    def __init__(self, client):
        """Init with a url that we can use"""
        self.client = client
        print("Initializing Spotify Client")
        spotify_token = tekore.request_client_token(
            os.getenv("Spotify_ClientID"), os.getenv("Spotify_ClientSecret")
        )
        self.client.spotify = tekore.Spotify(spotify_token, asynchronous=True)
        self.playlist_limit

    async def search_spotify(self, player, ctx, args: str):
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
        """
        try:
            from_url = tekore.from_url(args)
        except:
            embed = discord.Embed(
                title=f"Error",
                description=f"""```diff
- The spotify link {args} was not found. -""",
                timestamp=discord.utils.utcnow(),
                color=c_get_color("red"),
            )
            return await ctx.send(embed=embed, delete_after=10)

        if from_url[0] == "track":
            try:
                track = await self.bot.spotify.track(from_url[1])
            except:
                trackNF = discord.Embed(
                    title=f"Error",
                    description=f"""The Spotify link is invalid!""",
                    timestamp=discord.utils.utcnow(),
                    color=c_get_color("red"),
                )
                await ctx.send(embed=trackNF)

            title = track.name
            artist = track.artists[0].name
            query = f"{title} {artist}"

            results = await player.node.get_tracks(query)

            if not results or not results["tracks"]:
                nothing_found = discord.Embed(
                    title=f"Error",
                    description=f"""Sorry, but nothing was found for the search `{query}`""",
                    timestamp=discord.utils.utcnow(),
                    color=c_get_color("red"),
                )
                return await ctx.send(embed=nothing_found, delete_after=10)


            track = lavalink.models.AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)

        elif from_url[0] == "playlist":
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
                    color=c_get_color("red"),
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
                color=c_get_color("red"),
            )
            await ctx.send(embed=not_supported)


class Music(commands.Cog):
    """The music cog that plays all of our music"""

    def __init__(self, client):
        self.client = client
        self.search_prefix = client.config.get("Lavalink").get("Search")
        # This ensures the client isn't overwritten during cog reloads
        if not hasattr(
            client, "lavalink"
        ):
            client.lavalink = lavalink.Client(889672871620780082)
            # Host, Port, Password, Region, Name
            client.lavalink.add_node(
                "localhost", 2333, "BennyBotRoot", "na", "default-node"
            )

        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        """Cog unload handler. This removes any event hooks that were registered"""
        self.client.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        """A guild only check"""
        guild_check = ctx.guild is not None

        if guild_check:
            await self.ensure_voice(ctx)
            #  Ensure that the client and command author share a mutual voicechannel.

        return guild_check

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            embed = discord.Embed(
                title=f"Error",
                description=f"""```diff
- {error.original} -
```""",
                timestamp=discord.utils.utcnow(),
                color=c_get_color("red"),
            )
            await ctx.send(embed=embed)
            print(error)

    async def ensure_voice(self, ctx):
        """This check ensures that the client and command author are in the same voicechannel."""
        player = self.client.lavalink.player_manager.create(
            ctx.guild.id, endpoint=str(ctx.guild.region)
        )
        # Create returns a player if one exists, otherwise creates.
        # This line is important because it ensures that a player always exists for a guild.

        # Most people might consider this a waste of resources for guilds that aren't playing, but this is
        # the easiest and simplest way of ensuring players are created.

        # These are commands that require the client to join a voicechannel (i.e. initiating playback).
        # Commands such as volume/skip etc don't require the client to be in a voicechannel so don't need listing here.
        should_connect = ctx.command.name in ("play", "loop", "remove")

        if not ctx.author.voice or not ctx.author.voice.channel:
            # Our cog_command_error handler catches this and sends it to the voicechannel.
            # Exceptions allow us to "short-circuit" command invocation via checks so the
            # execution state of the command goes no further.
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
            # When this track_hook receives a "QueueEndEvent" from lavalink.py
            # it indicates that there are no tracks left in the player's queue.
            # To save on resources, we can tell the client to disconnect from the voicechannel.
            guild_id = int(event.player.guild_id)
            guild = self.client.get_guild(guild_id)

            await guild.voice_client.disconnect(force=True)

    @commands.command(
        name="play", 
        aliases=["p"]
    )
    @commands.cooldown(1.0, 1.5, commands.BucketType.user)
    async def play_cmd(self, ctx, *, args: str):
        """Searches and plays a song from a given query."""
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        query = args.strip("<>")
        # ytsearch or scsearch
        if not url_rx.match(query):
            # Treat as a regular search
            query = f"{self.search_prefix}:{query}"
        
        else:
            # Is a link...
            query = ""

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        # Results could be None if Lavalink returns an invalid response results['tracks'] could be an empty array if the query yielded no tracks
        if not results or not results["tracks"]:
            nothing_found = discord.Embed(
                title=f"Error",
                description=f"""Sorry, but nothing was found for the search `{query}`""",
                timestamp=discord.utils.utcnow(),
                color=c_get_color("red"),
            )
            return await ctx.send(embed=nothing_found, delete_after=10)

        embed = discord.Embed(color=c_get_color())

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        if results["loadType"] == "PLAYLIST_LOADED":
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
            ps_view = PlayerSelector(ctx, player, results["tracks"][:25])
            embed = discord.Embed(
                title=f"Select a Song to Play",
                description=f"""```asciidoc
= Showing Song Results =
[ {args} ]
```""",
                timestamp=discord.utils.utcnow(),
                color=c_get_color()
            )
            ps_view.play_embed = await ctx.send(embed=embed, view=ps_view)

    @commands.command(
        name="remove",
        description="""Remove a song from the queue""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        usage="Usage",
        aliases=["r"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def remove_cmd(self, ctx, index: int):
        """Remove command"""
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if not player.queue:
            return await ctx.send("Nothing queued.")

        track = player.queue[index - 1]

        del player.queue[index - 1]

        await ctx.send(
            f"Removed {index}. {track.title} [{track.author}] ({lavalink.format_time(track.duration)}) from the queue."
        )

    @commands.command(
        name="skip",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        usage="Usage",
        aliases=["s"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 3.0, commands.BucketType.user)
    async def skip_cmd(self, ctx):
        """Skip the song and move onto the next one"""
        # Get the player for this guild from cache.
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        await player.skip()

    @commands.command(
        name="loop",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        usage="Usage",
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

        view = LoopButton(False, player.repeat, player)

        embed = discord.Embed(
            title=f"""{c_get_emoji("regular", "loop")} {title}""",
            description=f"""{description}""",
            timestamp=discord.utils.utcnow(),
            color=c_get_color("aqua"),
        )
        view.bctx = await ctx.send(embed=embed, view=view)

    @commands.command(
        name="queue",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        usage="Usage",
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
                color=c_get_color("aqua"),
            )
            return await ctx.send(embed=embed)

        queue_visual = ""

        for count, track in enumerate(queue, 1):
            queue_visual = f"{queue_visual}\n{count}. {track.title} [{track.author}] ({lavalink.format_time(track.duration)})"

        embed = discord.Embed(
            title=f"Queue",
            description=f"""```md
{queue_visual}
```""",
            timestamp=discord.utils.utcnow(),
            color=c_get_color("green"),
        )
        embed.set_footer(text=f"""Add the total time and loop info here dumbass""")
        await ctx.send(embed=embed)

    @commands.command(
        name="np",
        description="""Description of Command""",
        help="""Long Help text for this command""",
        brief="""Short help text""",
        usage="Usage",
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
                title=f"",
                description=f"""Nothing is playing!
                Use `play` to queue a song!""",
                timestamp=discord.utils.utcnow(),
                color=c_get_color("aqua"),
            )
            await ctx.send(embed=nothing_playing)

        current = player.current

        embed = discord.Embed(
            title=f"{current.title} - {current.author}",
            url=current.uri,
            description=f"""Duration: {lavalink.format_time(current.duration)}""",
            timestamp=discord.utils.utcnow(),
            color=c_get_color(),
        )

        requester = self.client.get_user(current.requester)

        if not requester:
            requester = await self.client.fetch_user(current.requester)

        embed.set_footer(
            text=requester.display_name, icon_url=requester.display_avatar.url
        )

        embed.add_field(name="Other tings", value="Other tings", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="disconnect", aliases=["dc"])
    async def disconnect_cmd(self, ctx):
        """Disconnects the player from the voice channel and clears its queue."""
        player = self.client.lavalink.player_manager.get(ctx.guild.id)

        # Setting looping to false
        player.set_repeat(False)

        # Setting shuffling to false
        player.set_shuffle(False)

        if not player.is_connected:
            # We can't disconnect, if we're not connected.
            nc = discord.Embed(
                title=f"Error",
                description=f"""Not connected, join a voice channel and use the `play` command to get started!""",
                timestamp=discord.utils.utcnow(),
                color=c_get_color(),
            )
            return await ctx.send(embed=nc)

        if not ctx.author.voice or (
            player.is_connected
            and ctx.author.voice.channel.id != int(player.channel_id)
        ):
            # Abuse prevention. Users not in voice channels, or not in the same voice channel as the client
            # may not disconnect the client.
            embed = discord.Embed(
                title=f"Error",
                description=f""""You're not in my voicechannel!""",
                timestamp=discord.utils.utcnow(),
                color=c_get_color("red"),
            )
            return await ctx.send(embed=embed, delete_after=10)

        # Clear the queue to ensure old tracks don't start playing
        # when someone else queues something.
        player.queue.clear()
        # Stop the current track so Lavalink consumes less resources.
        await player.stop()
        # Disconnect from the voice channel.
        # await ctx.voice_client.cleanup()
        await ctx.voice_client.disconnect(force=True)
        dc = discord.Embed(
            title=f"Disconnected",
            description=f"""Disconnected successfully.""",
            timestamp=discord.utils.utcnow(),
            color=c_get_color("green"),
        )
        await ctx.send(embed=dc)


def setup(client):
    client.add_cog(Music(client))
