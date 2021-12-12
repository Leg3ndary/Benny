import itertools
import math

import asyncio
import discord
import discord.utils
import functools
import random
import youtube_dl
from async_timeout import timeout
from discord.ext import commands
from gears.style import c_get_color


# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ""


class VoiceError(Exception):
    """Voice Errors"""

    pass


class YTDLError(Exception):
    """YTDL Errors"""

    pass


class YTDLSource(discord.PCMVolumeTransformer):
    """Options"""

    YTDL_OPTIONS = {
        "format": "bestaudio/best",
        "extractaudio": True,
        "audioformat": "mp3",
        "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
        "restrictfilenames": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto",
        "source_address": "0.0.0.0",
    }

    FFMPEG_OPTIONS = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(
        self,
        ctx: commands.Context,
        source: discord.FFmpegPCMAudio,
        *,
        data: dict,
        volume: float = 0.5,
    ):
        """Init with everything we need"""
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get("uploader")
        self.uploader_url = data.get("uploader_url")
        date = data.get("upload_date")
        self.upload_date = date[6:8] + "." + date[4:6] + "." + date[0:4]
        self.title = data.get("title")
        self.thumbnail = data.get("thumbnail")
        self.description = data.get("description")
        self.duration = self.parse_duration(int(data.get("duration")))
        self.tags = data.get("tags")
        self.url = data.get("webpage_url")
        self.views = data.get("view_count")
        self.likes = data.get("like_count")
        self.dislikes = data.get("dislike_count")
        self.stream_url = data.get("url")

    def __str__(self):
        return f"""```asciidoc
= {self.title} =
[ {self.uploader} ]
```"""

    @classmethod
    async def create_source(
        cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None
    ):
        """Create a source for music"""
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(
            cls.ytdl.extract_info, search, download=False, process=False
        )
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError(f"Couldn't find anything that matches `{search}`")

        if "entries" not in data:
            process_info = data
        else:
            process_info = None
            for entry in data["entries"]:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError(f"Couldn't find anything that matches `{search}`")

        webpage_url = process_info["webpage_url"]
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError(f"Couldn't fetch `{webpage_url}`")

        if "entries" not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info["entries"].pop(0)
                except IndexError:
                    raise YTDLError(
                        f"Couldn't retrieve any matches for `{webpage_url}`"
                    )

        return cls(
            ctx, discord.FFmpegPCMAudio(info["url"], **cls.FFMPEG_OPTIONS), data=info
        )

    @staticmethod
    def parse_duration(duration: int):
        """Parses the duration into a human readable form"""

        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append(f"{days} days")
        if hours > 0:
            duration.append(f"{hours} hours")
        if minutes > 0:
            duration.append(f"{minutes} minutes")
        if seconds > 0:
            duration.append(f"{seconds} seconds")

        return ", ".join(duration)


class Song:
    """Song class which represents a singular song"""

    __slots__ = ("source", "requester")

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    async def create_embed(self):
        check = "<:check:891088754176036885>"
        cancel = "<:cancel:891088754599682059>"
        embed = discord.Embed(
            title="<:pp:891088754754871316> Now Playing",
            description=f"""```asciidoc
= {self.source.title} =
[ {self.source.uploader} ]
```""",
            url=self.source.uploader_url,
            color=await c_get_color(),
        )
        embed.add_field(name="Duration", value=self.source.duration)
        embed.add_field(
            name="Info",
            value=f""":eyes: {self.source.views:,}
            {check} {self.source.likes:,} 
            {cancel} {self.source.dislikes:,}
            """,
        )
        embed.set_thumbnail(url=self.source.thumbnail)
        embed.set_footer(text=f"Requested by {self.requester.name}")

        return embed


class SongQueue(asyncio.Queue):
    """Song queue class"""

    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    """Voice states"""

    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()
            self.now = None

            if not self.loop:
                """
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                #"""
                try:
                    # 3 minute timeout
                    async with timeout(180):
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    return

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(
                embed=await self.current.create_embed()
            )

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    """The music cog"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage(
                "This command can't be used in DM channels."
            )

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        embed_cog_error = discord.Embed(
            title="Error",
            description=f"""```diff
- {str(error)} -
```""",
            timestamp=discord.utils.utcnow(),
            color=await c_get_color("red"),
        )
        await ctx.send(embed=embed_cog_error)

    @commands.command(name="connect", aliases=["join"], invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Join a voice channel"""

        await ctx.message.add_reaction("<:pp:891088754754871316>")

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            return await ctx.voice_state.voice.move_to(destination)

        ctx.voice_state.voice = await destination.connect()

        embed = discord.Embed(
            title=f"Connected to {destination}",
            timestamp=discord.utils.utcnow(),
            color=await c_get_color("green"),
        )
        await ctx.send(embed=embed, delete_after=3)

    @commands.command(name="summon")
    @commands.has_permissions(manage_guild=True)
    async def _summon(
        self, ctx: commands.Context, *, channel: discord.VoiceChannel = None
    ):
        """Summon the bot to a channel"""
        await ctx.message.add_reaction("<:pp:891088754754871316>")
        if not channel and not ctx.author.voice:
            raise VoiceError(
                "You are neither connected to a voice channel nor specified a channel to join."
            )

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            return await ctx.voice_state.voice.move_to(destination)

        ctx.voice_state.voice = await destination.connect()

        embed = discord.Embed(
            title=f"<:pp:891088754754871316> Joined {destination}",
            timestamp=discord.utils.utcnow(),
            color=await c_get_color("green"),
        )
        await ctx.send(embed=embed, delete_after=5)

    @commands.command(name="leave", aliases=["disconnect", "dc"])
    async def _leave(self, ctx: commands.Context):
        """Leave the channel"""
        if not ctx.voice_state.voice:
            embed_no_vc = discord.Embed(
                title="Error",
                description="""Either you or me aren't connected to a voice channel!""",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("red"),
            )
            return await ctx.send(embed=embed_no_vc, delete_after=5)

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]
        embed = discord.Embed(
            title=f"Disconnected",
            timestamp=discord.utils.utcnow(),
            color=await c_get_color("green"),
        )
        await ctx.send(embed=embed, delete_after=5)

    @commands.command(name="volume")
    @commands.has_permissions(manage_guild=True)
    async def _volume(self, ctx: commands.Context, *, volume: int):
        """Change the musics volume"""
        if not ctx.voice_state.is_playing:
            embed_nothing_playing = discord.Embed(
                title="Error",
                description="""Nothing's being played right now""",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("blue"),
            )
            return await ctx.send(embed=embed_nothing_playing, delete_after=5)

        if 0 > volume > 100:
            embed_volume_max = discord.Embed(
                title="Error",
                description="""Volume must be between 0 and 100""",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("red"),
            )
            return await ctx.send(embed=embed_volume_max, delete_after=5)

        ctx.voice_state.volume = volume / 100

        await ctx.message.add_reaction("<:volume:820031965327523871>")
        embed_volume_set = discord.Embed(
            title="<:volume:820031965327523871> - Volume Change",
            description=f"""Volume set to {volume}%""",
            timestamp=discord.utils.utcnow(),
            color=await c_get_color("blue"),
        )
        return await ctx.send(embed=embed_volume_set, delete_after=5)

    @commands.command(name="now", aliases=["current", "playing", "np"])
    async def _now(self, ctx: commands.Context):
        """Show what's currently playing"""
        await ctx.send(embed=await ctx.voice_state.current.create_embed())

    @commands.command(name="pause")
    async def _pause(self, ctx: commands.Context):
        """Pause the music"""
        if ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction("<:pause:820003279941271592>")
            embed_paused = discord.Embed(
                title="<:pause:820003279941271592> Paused",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("yellow"),
            )
            await ctx.send(embed=embed_paused, delete_after=5)

    @commands.command(name="resume", aliases=["unpause"])
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song"""

        if ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction("<:pp:891088754754871316>")
            embed_resumed = discord.Embed(
                title="<:pp:891088754754871316> - Resumed",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("yellow"),
            )
            await ctx.send(embed=embed_resumed, delete_after=5)

    @commands.command(name="stop")
    @commands.has_permissions(manage_guild=True)
    async def _stop(self, ctx: commands.Context):
        """Stop the music that's currently playing"""
        ctx.voice_state.songs.clear()

        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction("<:stop:891088754134089749>")
            embed_stopped = discord.Embed(
                title="<:stop:891088754134089749> Stopped",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("red"),
            )
            await ctx.send(embed=embed_stopped, delete_after=5)

    @commands.command(name="skip", aliases=["s"])
    async def _skip(self, ctx: commands.Context):
        """Vote to skip a song. The requester can automatically skip.
        3 skip votes are needed for the song to be skipped."""
        if ctx.author.voice == None:
            embed_novc = discord.Embed(
                title="You aren't in the same voice channel as me!",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("red"),
            )
            return await ctx.send(embed=embed_novc, delete_after=5)

        if ctx.author.voice.channel != ctx.voice_client.channel:
            embed_not_same_channel = discord.Embed(
                title="We aren't in the same voice channel!",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("red"),
            )
            return await ctx.send(embed=embed_not_same_channel, delete_after=5)

        if not ctx.voice_state.is_playing:
            embed_not_playing_anything = discord.Embed(
                title="Error",
                description="Not playing any music right now...",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("red"),
            )
            return await ctx.send(embed=embed_not_playing_anything)

        voter = ctx.message.author

        if voter == ctx.voice_state.current.requester:
            await ctx.message.add_reaction("<:right:891088754494808134>")
            embed_skipped_br = discord.Embed(
                title="<:right:891088754494808134> Skipped by Requester",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("orange"),
            )
            await ctx.send(embed=embed_skipped_br, delete_after=5)
            ctx.voice_state.skip()
            return

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            total_voters = int(len(ctx.author.voice.channel.members))
            votes_needed = round((total_voters / 2) + (total_voters / 25))

            print(total_voters)
            print(votes_needed)

            if total_votes >= votes_needed:
                await ctx.message.add_reaction("<:right:891088754494808134>")
                embed_vote_skipped = discord.Embed(
                    title="<:right:891088754494808134> Skipped by Vote",
                    timestamp=discord.utils.utcnow(),
                    color=await c_get_color("orange"),
                )
                await ctx.send(embed=embed_vote_skipped, delete_after=5)
                ctx.voice_state.skip()

            else:
                await ctx.message.add_reaction("<:check:891088754176036885>")
                embed_skip_vote_add = discord.Embed(
                    title="<:check:891088754176036885> Skip Vote Added",
                    description=f"Skip vote added, currently at **{total_votes}/{votes_needed}**",
                    timestamp=discord.utils.utcnow(),
                    color=await c_get_color("green"),
                )
                await ctx.send(embed=embed_skip_vote_add, delete_after=5)
        else:
            embed_already_voted = discord.Embed(
                title="Error",
                description=f"You've already voted to skip this song!",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("red"),
            )
            await ctx.send(embed=embed_already_voted, delete_after=5)

    @commands.command(name="queue", aliases=["q"])
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """View the current queue"""
        if len(ctx.voice_state.songs) == 0:
            embed_empty_queue = discord.Embed(
                title="Error",
                description=f"The queue is empty",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("red"),
            )
            return await ctx.send(embed=embed_empty_queue)

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        if page > pages:
            page = pages

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ""
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += f"{i + 1}. {song.source.title}\n"

        embed_queue = discord.Embed(
            title=f"<:search:891088754121506867> {ctx.guild.name}'s Queue",
            description=f"""**{len(ctx.voice_state.songs)} Tracks:**
```md
{queue}
```""",
            color=await c_get_color("blue"),
        )
        embed_queue.set_author(name=f"Viewing page {page}/{pages}")
        embed_queue.set_footer(
            text="Use >play to queue more songs, use >queue <number> to view a different page!"
        )
        await ctx.send(embed=embed_queue)

    @commands.command(name="shuffle")
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            embed_empty_queue = discord.Embed(
                title="Error",
                description="You have an empty queue",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color(),
            )
            return await ctx.send(embed=embed_empty_queue, delete_after=5)

        if len(ctx.voice_state.songs) == 1:
            embed_one_song = discord.Embed(
                title="Error",
                description="You only have 1 song in your queue!",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color(),
            )
            return await ctx.send(embed=embed_one_song, delete_after=5)

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction("<:search:891088754121506867>")
        embed = discord.Embed(
            title="<:search:891088754121506867> - Shuffled Queue",
            timestamp=discord.utils.utcnow(),
            color=await c_get_color("black"),
        )
        await ctx.send(embed=embed, delete_after=5)

    @commands.command(name="remove")
    async def _remove(self, ctx: commands.Context, index: int):
        """Remove something from the queue"""

        if len(ctx.voice_state.songs) == 0:
            embed_empty_queue = discord.Embed(
                title="Error",
                description="You have an empty queue",
                timestamp=discord.utils.utcnow(),
                color=await c_get_color("red"),
            )
            await ctx.send(embed=embed_empty_queue, delete_after=5)

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction("<:left:891088754398330991>")

        embed = discord.Embed(
            title=f"<:left:891088754398330991> Song {index} Removed",
            timestamp=discord.utils.utcnow(),
            color=await c_get_color("blue"),
        )
        await ctx.send(embed=embed, delete_after=5)

    @commands.command(name="loop")
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song.

        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send("Nothing being played at the moment.")

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction("<:search:891088754121506867>")
        embed = discord.Embed(
            title=f"<:search:891088754121506867> - Looping/Unlooping Song",
            timestamp=discord.utils.utcnow(),
            color=await c_get_color("orange"),
        )
        await ctx.send(embed=embed, delete_after=5)

    @commands.command(name="play")
    async def _play(self, ctx: commands.Context, *, search: str):
        """Play a song"""
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as error:
                embed_error = discord.Embed(
                    title="Error",
                    description=f"""An Error Occured while processing this request, if the issue persists, contact _Leg3ndary#3109
```diff
- {str(error)}
```""",
                )
                await ctx.send(embed_error)
            else:
                song = Song(source)
                await ctx.message.add_reaction("<:play_button:820007755922014240>")

                await ctx.voice_state.songs.put(song)
                embed_queued = discord.Embed(
                    title="<:play_button:820007755922014240> - Queued Song",
                    description=f"""{str(source)}""",
                    timestamp=discord.utils.utcnow(),
                    color=await c_get_color("green"),
                )
                await ctx.send(embed=embed_queued, delete_after=5)

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("You are not connected to any voice channel.")

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError("Bot is already in a voice channel.")


def setup(bot):
    bot.add_cog(Music(bot))
