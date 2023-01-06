import asyncio
import datetime
import os
import random
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import asqlite
import discord
import discord.utils
import tekore
import wavelink
from discord.ext import commands
from gears import style, util
from gears.music_exceptions import NotConnected, NothingPlaying, QueueEmpty, QueueFull
from musescore_scraper import MuseScraper
from wavelink.ext import spotify


class Player(wavelink.Player):
    """
    Custom player class that we use
    """

    def __init__(self, dj: discord.Member, channel: discord.VoiceChannel) -> None:
        """
        Init with stuff
        """
        super().__init__()
        self.dj: discord.Member = dj
        self.channel: discord.VoiceChannel = channel
        self.queue: wavelink.Queue = wavelink.Queue(max_size=250)
        self.looping: bool = False

    async def request(self, track: wavelink.Track) -> None:
        """
        Requests a song without having any of the other troublesome stuff
        """
        if self.queue.is_full:
            raise QueueFull()
        if self.queue.is_empty and not self.track:
            await self.play(track)
        else:
            self.queue.put(track)

    async def skip(self) -> None:
        """
        Skip the currently playing track, just an alias
        """
        if self.queue.is_empty and not self.track:
            raise NothingPlaying()
        await self.stop()

    async def shuffle(self) -> None:
        """
        Shuffle the queue
        """
        if self.queue.is_empty:
            raise QueueEmpty()
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
        """
        Loop the queue
        """
        if self.queue.is_empty and not self.is_playing():
            raise QueueEmpty()
        self.looping = not self.looping


class PlayerDropdown(discord.ui.Select):
    """
    Shows up to 25 songs in a Select so we can see it
    """

    def __init__(
        self, ctx: commands.Context, player: Player, songs: List[wavelink.Track]
    ) -> None:
        """
        Constructing the dropdown view
        """
        self.ctx = ctx
        self.player = player
        self.songs = songs
        options = []
        for count, song in enumerate(songs):
            options.append(
                discord.SelectOption(
                    emoji=style.Emoji.REGULAR.music,
                    label=song.title,
                    description=f"""{song.author} - Duration: {duration(song.length)}""",
                    value=count,
                )
            )
        super().__init__(
            placeholder="Select a Song",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """
        Callback for the queue
        """
        track = self.songs[int(self.values[0])]

        total = track.length

        for queued_track in self.player.queue._queue:
            if isinstance(queued_track, wavelink.PartialTrack):
                pass
            else:
                total += queued_track.length

        if self.player.queue.count == 0:
            title = "Playing now"
            playing_message = ""
        elif self.player.queue.count == 1:
            title = "Up Next"
            playing_message = f"\nPlaying {discord.utils.format_dt(datetime.datetime.now() + datetime.timedelta(seconds=total), style='R')}"
        else:
            title = f"Queue Position {self.player.queue.count + 1 if self.player.queue.count != 0 and (not self.player.is_playing() or self.player.is_paused()) else 'Unknown'}"
            playing_message = f"\nPlaying {discord.utils.format_dt(datetime.datetime.now() + datetime.timedelta(seconds=total), style='R')}"

        embed = discord.Embed(
            title=f"Track Queued - {title}",
            url=track.uri,
            description=f"""```asciidoc
[ {track.title} ]
= Duration: {duration(track.length)} =
```{playing_message}""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        embed.set_author(name=track.author)
        embed.set_footer(
            text=self.ctx.author.display_name,
            icon_url=self.ctx.author.display_avatar.url,
        )

        await self.player.request(track)
        self.ctx.bot.dispatch("music_add_to_recent", str(self.ctx.author.id), track)
        await interaction.response.edit_message(embed=embed, view=None)
        self.view.stop()


class RecentlyPlayedDropdown(discord.ui.Select):
    """
    Display recently played tracks
    """

    def __init__(
        self, ctx: commands.Context, player: Player, songs: List[wavelink.Track]
    ) -> None:
        """
        Constructing the dropdown view
        """
        self.ctx = ctx
        self.player = player
        self.songs = songs
        options = []

        for count, song in enumerate(songs):
            options.append(
                discord.SelectOption(
                    emoji=style.Emoji.REGULAR.music,
                    label=song.title,
                    description=f"""{song.author} - Duration: {duration(song.length)}""",
                    value=count,
                )
            )
        super().__init__(
            placeholder="Recently Played",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """
        Callback for the queue
        """
        track = self.songs[int(self.values[0])]

        total = track.length

        for queued_track in self.player.queue._queue:
            if isinstance(queued_track, wavelink.PartialTrack):
                pass
            else:
                total += queued_track.length

        if self.player.queue.count == 0 and self.player.is_playing():
            title = "Playing now"
            playing_message = ""
        elif self.player.queue.count == 1:
            title = "Up Next"
            playing_message = f"\nPlaying {discord.utils.format_dt(datetime.datetime.now() + datetime.timedelta(seconds=total), style='R')}"
        else:
            title = f"Queue Position {self.player.queue.count + 1 if self.player.queue.count != 0 and (not self.player.is_playing() or self.player.is_paused()) else 'Unknown'}"
            playing_message = f"\nPlaying {discord.utils.format_dt(datetime.datetime.now() + datetime.timedelta(seconds=total), style='R')}"

        embed = discord.Embed(
            title=f"Track Queued - {title}",
            url=track.uri,
            description=f"""```asciidoc
[ {track.title} ]
= Duration: {duration(track.length)} =
```{playing_message}""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        embed.set_author(name=track.author)
        embed.set_footer(
            text=self.ctx.author.display_name,
            icon_url=self.ctx.author.display_avatar.url,
        )

        await self.player.request(track)
        self.ctx.bot.dispatch("music_add_to_recent", str(self.ctx.author.id), track)
        await interaction.response.edit_message(embed=embed, view=None)
        self.view.stop()


class PlayerSelector(discord.ui.View):
    """
    Select a song based on what we show from track results.
    """

    def __init__(
        self,
        ctx: commands.Context,
        node: wavelink.Node,
        player: Player,
        songs: List[wavelink.Track],
    ) -> None:
        """
        Constructing the player selector
        """
        super().__init__(timeout=60)
        self.ctx = ctx
        self.node = node
        self.player = player
        self.add_item(PlayerDropdown(ctx, player, songs))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        If the interaction isn't by the user, return a fail.
        """
        if interaction.user != self.ctx.author:
            return False
        return True

    async def on_timeout(self) -> None:
        """
        On timeout make this look cool
        """
        for item in self.children:
            item.disabled = True

    async def add_recently_played(self, cursor: asqlite.Cursor) -> None:
        """
        Add recently played to the view
        """
        songs = await cursor.execute(
            """SELECT recent FROM recently_played WHERE id = ?;""",
            (str(self.ctx.author.id)),
        )
        songs = (await songs.fetchone())[0]
        if songs:
            songs = [
                await self.node.build_track(wavelink.Track, song)
                for song in songs.split("|")
            ]
            self.add_item(RecentlyPlayedDropdown(self.ctx, self.player, songs))

    @discord.ui.button(
        emoji=style.Emoji.REGULAR.cancel,
        label="Cancel",
        style=discord.ButtonStyle.danger,
        row=2,
    )
    async def button_callback(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Delete the message if clicked
        """
        await interaction.message.delete()


class QueueDropdown(discord.ui.Select):
    """
    Shows up to 25 songs in a Select so we can see it and skip to it and stuff
    """

    def __init__(
        self,
        ctx: commands.Context,
        player: Player,
        songs: List[wavelink.Track],
        page_num: int,
    ) -> None:
        """
        Construct the queue dropdown view
        """
        self.ctx = ctx
        self.player = player
        self.songs = songs
        options = []
        self.page_num = page_num

        for counter, song in enumerate(songs):
            options.append(
                discord.SelectOption(
                    emoji=style.Emoji.REGULAR.music,
                    label=song.title,
                    description=f"""{song.author} - Duration: {duration(song.length)}""",
                    value=counter,
                )
            )

        super().__init__(
            placeholder=f"View Queue - Page {self.page_num}",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """
        Callback for the queue
        """
        track = self.songs[int(self.values[0])]

        embed = discord.Embed(
            title=f"Viewing Track {self.values[0]}",
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

        await interaction.response.edit_message(embed=embed, view=None)


class QueueView(discord.ui.View):
    """
    Display all items in our queue, let you skip to any song
    """

    def __init__(
        self, ctx: commands.Context, player: Player, songs: List[wavelink.Track]
    ) -> None:
        """
        Construct the queue view with dropdown attached
        """
        self.ctx = ctx
        super().__init__(timeout=60)

        self.add_item(QueueDropdown(ctx, player, songs, 1))  # not finished

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        If the interaction isn't by the user, return a fail.
        """
        if interaction.user != self.ctx.author:
            return False
        return True

    async def on_timeout(self) -> None:
        """
        On timeout make this look cool
        """
        for item in self.children:
            item.disabled = True


class FilterSpinView(discord.ui.View):
    """
    Display a ui for spinning!
    """

    def __init__(self, ctx: commands.Context, player: Player) -> None:
        """
        Construct the spinny thing :)
        """
        self.ctx = ctx
        self.player = player
        self.spin: float = 0.0
        super().__init__()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        If the interaction isn't by the user, return a fail.
        """
        if interaction.user != self.ctx.author:
            return False
        return True

    async def on_timeout(self) -> None:
        """
        On timeout make this look cool
        """
        for item in self.children:
            item.disabled = True

    async def set_spin(self) -> None:
        """
        Set the spin to the self value
        """
        rotation = wavelink.Rotation(speed=self.spin)
        await self.player.set_filter(wavelink.Filter(rotation=rotation), seek=True)

    async def edit_spin_embed(self, interaction: discord.Interaction) -> None:
        """
        Edit the spin embed
        """
        self.spin = min(self.spin, 5.0)
        if self.spin < -5.0:
            self.spin = -5.0
        await self.set_spin()

        embed = discord.Embed(
            title="Spin Mode",
            description=f"""Set a spin mode below!
            
            Note the max values of this are 5 and -5, don't get too dizzy!
            
            **Spinning:** {"No direction" if self.spin == 0 else ("Clockwise" if self.spin > 0 else "Counter ClockWise")}
            **Speed** {str(self.spin)}""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.PURPLE,
        )
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(
        emoji=style.Emoji.REGULAR.left, label="-1", style=discord.ButtonStyle.danger
    )
    async def button2_callback(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        -1 button
        """
        self.spin -= 1
        await self.edit_spin_embed(interaction)

    @discord.ui.button(
        emoji=style.Emoji.REGULAR.left, label="-0.1", style=discord.ButtonStyle.danger
    )
    async def button1_callback(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        -0.1 button
        """
        self.spin -= 0.1
        await self.edit_spin_embed(interaction)

    @discord.ui.button(
        emoji=style.Emoji.REGULAR.stop, label="Reset", style=discord.ButtonStyle.grey
    )
    async def button3_callback(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Reset button
        """
        self.spin = 0.0
        await self.edit_spin_embed(interaction)

    @discord.ui.button(
        emoji=style.Emoji.REGULAR.right, label="+0.1", style=discord.ButtonStyle.green
    )
    async def button4_callback(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        +0.1 button
        """
        self.spin += 0.1
        await self.edit_spin_embed(interaction)

    @discord.ui.button(
        emoji=style.Emoji.REGULAR.right, label="+1", style=discord.ButtonStyle.green
    )
    async def button5_callback(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        +1 button
        """
        self.spin += 1
        await self.edit_spin_embed(interaction)


class MusescoreDropdown(discord.ui.Select):
    """
    Shows up to 25 sheets in a Select so you can choose one to download
    """

    def __init__(
        self,
        ctx: commands.Context,
        ams: MuseScraper,
        sheets: None,  # List[QueriedSheetMusic],
    ) -> None:
        """
        Construct the queue dropdown view
        """
        self.ctx = ctx
        self.ams = ams
        options = []

        self.sheets = sheets
        for counter, sheet in enumerate(sheets[:25]):
            options.append(
                discord.SelectOption(
                    label=sheet.title,
                    description=f"""{sheet.author} - Pages: {sheet.pages} - Playtime: {sheet.ttp}""",
                    value=counter,
                )
            )

        super().__init__(
            placeholder="Select a Sheet to Download",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """
        Callback for the queue
        """
        sheet = self.sheets[int(self.values[0])]
        embed = discord.Embed(
            title=f"Viewing Sheet {sheet.title}",
            url=sheet.url,
            description=f"""```yaml
            Author   : {sheet.author}
            Parts    : {sheet.parts}
            Pages    : {sheet.pages}
            Length   : {sheet.ttp}
            Views    : {sheet.views}
            Favorites: {sheet.favorites}
            Votes    : {sheet.votes}
            ```""",
            timestamp=discord.utils.utcnow(),
            color=0x3269BC,
        )
        embed.set_footer(
            text=self.ctx.author.display_name,
            icon_url=self.ctx.author.display_avatar.url,
        )
        await interaction.response.edit_message(
            embed=embed, view=MusescoreDownload(self.ctx, self.ams, sheet, self)
        )


class MusescoreView(discord.ui.View):
    """
    Display all sheets found during a search and display them
    """

    def __init__(
        self,
        ctx: commands.Context,
        ams: MuseScraper,
        sheets: None,  # List[QueriedSheetMusic],
    ) -> None:
        """
        Construct the sheets view with dropdown attached
        """
        self.ctx = ctx
        super().__init__(timeout=60)

        self.add_item(MusescoreDropdown(ctx, ams, sheets))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        If the interaction isn't by the user, return a fail.
        """
        if interaction.user != self.ctx.author:
            return False
        return True

    async def on_timeout(self) -> None:
        """
        On timeout make this look cool
        """
        for item in self.children:
            item.disabled = True

        embed = discord.Embed(
            title="Viewing Sheets",
            description="""Timed out""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.RED,
        )
        await self.play_embed.edit(embed=embed, view=self)

    @discord.ui.button(
        emoji=style.Emoji.REGULAR.cancel,
        label="Cancel",
        style=discord.ButtonStyle.danger,
        row=2,
    )
    async def button_callback(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Delete the message if clicked
        """
        await self.ctx.message.delete()


class MusescoreDownload(discord.ui.View):
    """
    Provide a download button
    """

    def __init__(
        self,
        ctx: commands.Context,
        ams: MuseScraper,
        sheet: None,  # QueriedSheetMusic,
        original_view: MusescoreView,
    ) -> None:
        """
        Construct the download view attached
        """
        self.ctx = ctx
        self.ams = ams
        self.sheet = sheet
        self.ov = original_view
        super().__init__(timeout=60)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        If the interaction isn't by the user, return a fail.
        """
        if interaction.user != self.ctx.author:
            return False
        return True

    async def on_timeout(self) -> None:
        """
        On timeout make this look cool
        """
        for item in self.children:
            item.disabled = True

    @discord.ui.button(
        emoji=style.Emoji.REGULAR.check,
        label="Download",
        style=discord.ButtonStyle.green,
    )
    async def download_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Download and send the pdf if clicked
        """
        embed = discord.Embed(
            title="Downloading...",
            description="""Please be patient, this may take a while.""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREY,
        )
        await self.ctx.edit(embed=embed)
        path = await self.ams.to_pdf(self.sheet.url)
        embed = discord.Embed(
            title="Downloaded",
            description="""This will remain on discord as long as you save the original message, enjoy!""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        await self.ctx.edit(
            embed=embed, file=discord.File(path, filename=f"{self.sheet.title}.pdf")
        )

    @discord.ui.button(
        emoji=style.Emoji.REGULAR.cancel,
        label="Cancel",
        style=discord.ButtonStyle.danger,
    )
    async def cancel_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Delete the message if clicked
        """
        await self.play_embed.delete()
        await interaction.response.send_message("Cancelled", ephemeral=True)


def duration(seconds: float) -> str:
    """
    Return a human readable duration because
    """
    return util.remove_zcs(str(datetime.timedelta(seconds=seconds)))


class Music(commands.Cog):
    """
    Music commands, join a voice channel and start listening with the play command
    """

    COLOR = style.Color.PINK
    ICON = "<a:_:992130768270790718>"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Construct the music cog
        """
        self.bot = bot
        self.wavelink: wavelink.Node = None
        self.musicDB: asqlite.Connection = None
        self.disconnect_tasks: Dict[str, asyncio.Task] = {}

        app_token = tekore.request_client_token(
            bot.config.get("Spotify").get("ID"), bot.config.get("Spotify").get("Secret")
        )
        self.spotify = tekore.Spotify(
            token=app_token, asynchronous=True, max_limits_on=True
        )

    async def connect_nodes(self) -> None:
        """
        Connect to our wavelink nodes.
        """
        if not self.bot.MUSIC_ENABLED:
            return

        if hasattr(self.bot, "wavelink"):
            self.wavelink = self.bot.wavelink

        else:
            self.bot.wavelink = await wavelink.NodePool.create_node(
                bot=self.bot,
                host="localhost",
                port=2333,
                region="na",
                password="BennyBotRoot",
                identifier="BennyMusic",
                spotify_client=spotify.SpotifyClient(
                    client_id=self.bot.config.get("Spotify").get("ID"),
                    client_secret=self.bot.config.get("Spotify").get("Secret"),
                ),
            )
            self.wavelink: wavelink.Node = self.bot.wavelink

    async def get_player(self, ctx: commands.Context) -> Optional[Player]:
        """
        Create a player and connect cls
        """
        if not ctx.author.voice:
            raise NotConnected()
        if not ctx.voice_client:
            player: Player = await ctx.author.voice.channel.connect(
                cls=Player(dj=ctx.author, channel=ctx.author.voice.channel),
                self_deaf=True,
                self_mute=False,
            )
        else:
            player: Player = ctx.voice_client

        return player

    @commands.Cog.listener()
    async def on_connect_wavelink(self) -> None:
        """
        On cog load do stuff
        """
        await self.connect_nodes()
        self.musicDB = await asqlite.connect("Databases/music.db")
        await self.musicDB.execute(
            """
            CREATE TABLE IF NOT EXISTS recently_played (
                id  TEXT NOT NULL
                    PRIMARY KEY,
                recent TEXT NOT NULL
            );
            """
        )
        await self.musicDB.commit()
        await self.bot.blogger.load("Recently Played")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        """
        Event fired when a node has finished connecting.
        """
        await self.bot.blogger.connect(f"{node.identifier} is ready.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(
        self, player: Player, track: wavelink.Track, reason: str
    ) -> None:
        """
        On end, check if the queue has another song to play if not disconnect after 5 min
        """
        if player.queue.is_empty:
            if player.looping:
                await player.request(track)
            elif not player.is_playing() or not player.is_paused():
                self.disconnect_tasks[player.channel.id] = self.bot.loop.create_task(
                    self.await_disconnect(player)
                )
        else:
            if player.looping:
                await player.request(track)
            else:
                await player.play(player.queue.get())

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """
        Check if the bot should disconnect
        """
        if after.channel or member.guild.voice_client is None:
            return
        if before.channel and before.channel.id not in self.disconnect_tasks:
            player = member.guild.voice_client
            self.disconnect_tasks[player.channel.id] = self.bot.loop.create_task(
                self.await_disconnect(player)
            )
        if after.channel and after.channel.id in self.disconnect_tasks:
            if not member.bot:
                self.disconnect_tasks[before.channel.id].cancel()
                del self.disconnect_tasks[before.channel.id]

    async def await_disconnect(self, player: Player) -> None:
        """
        Wait for the player to disconnect
        """
        await asyncio.sleep(180)
        if (
            player.is_connected()
            and (not player.is_playing() or not player.is_paused())
            and player.queue.is_empty
            and len(player.channel.members) == 1
        ):
            try:
                await player.disconnect()
            except Exception as e:
                await self.bot.blogger.error(e)

    async def handle_spotify_track(
        self, ctx: commands.Context, player: Player, decoded: Dict[str, Any]
    ) -> None:
        """
        Handle a spotify track
        """
        track = await spotify.SpotifyTrack.search(
            query=decoded["id"], return_first=True
        )
        await player.request(track)
        ctx.bot.dispatch("music_add_to_recent", str(ctx.author.id), track)

        embed = discord.Embed(
            title=f"{style.Emoji.REGULAR.spotify} Playing Track From Spotify",
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
        await ctx.reply(embed=embed)

    async def handle_spotify_playlist(
        self, ctx: commands.Context, player: Player, decoded: Dict[str, Any]
    ) -> None:
        """
        Handle a spotify playlist
        """
        length = int(
            (await self.spotify.playlist(decoded["id"], fields="tracks(total)"))
            .get("tracks")
            .get("total")
        )

        if length >= 100:
            raise commands.BadArgument(
                "You may only add up to 100 songs through spotify playlists at this time."
            )

        playlist: tekore.model.FullPlaylist = await self.spotify.playlist(decoded["id"])

        embed = discord.Embed(
            title=f"{style.Emoji.REGULAR.spotify} Queueing {playlist.name}",
            description=f"""```asciidoc
[ Adding {length} Songs ]
= Duration: Calculating =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREY,
        )
        embed.set_author(
            name=playlist.owner.display_name if playlist.owner else "Featured Playlist"
        )
        embed.set_footer(
            text=ctx.author.display_name,
            icon_url=ctx.author.display_avatar.url,
        )
        if playlist.images[0].url:
            embed.set_thumbnail(url=playlist.images[0].url)

        sent = await ctx.reply(embed=embed)

        total_dur = 0
        async for song in spotify.SpotifyTrack.iterator(query=decoded["id"]):
            await player.request(song)
            total_dur += song.length

        finished = discord.Embed(
            title=f"{style.Emoji.REGULAR.spotify} Playing {playlist.name}",
            url=playlist.href,
            description=f"""```asciidoc
[ Added {length} Songs ]
= Duration: {duration(total_dur)} =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        embed.set_author(
            name=playlist.owner.display_name if playlist.owner else "Featured Playlist"
        )
        embed.set_footer(
            text=ctx.author.display_name,
            icon_url=ctx.author.display_avatar.url,
        )
        await sent.edit(embed=finished)

    async def add_to_recent(self, user_id: str, track: wavelink.Track) -> None:
        """
        Add a track to the recently played table
        """
        async with self.musicDB.cursor() as cursor:
            previous = await cursor.execute(
                """
                SELECT recent FROM recently_played WHERE id = ?;
                """,
                (user_id,),
            )
            previous = (await previous.fetchone())[0].split("|")
            if previous:
                if track.id == previous[0]:
                    return
                if len(previous) >= 25:
                    previous.pop(0)
                previous.append(track.id)

                new = "|".join(previous)
                await cursor.execute(
                    """
                    UPDATE recently_played SET recent = ? WHERE id = ?;
                    """,
                    (new, user_id),
                )
            else:
                await cursor.execute(
                    """
                    INSERT INTO recently_played VALUES (?, ?);
                    """,
                    (user_id, track.id),
                )
            await cursor.commit()

    @commands.Cog.listener()
    async def on_music_add_to_recent(self, user_id: str, track: wavelink.Track) -> None:
        """
        Add a track to the recently played table
        """
        await self.add_to_recent(user_id, track)

    @commands.hybrid_command(
        name="play",
        description="""Play a song or place it in queue""",
        help="""Play a song or request in the queue""",
        brief="Play a song",
        aliases=["p"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def play_cmd(self, ctx: commands.Context, *, search: str) -> None:
        """
        Play a song with the given search query.

        If not connected, connect to our voice channel.
        """
        player = await self.get_player(ctx)

        decoded = spotify.decode_url(search)

        if decoded:
            if decoded["type"] == spotify.SpotifySearchType.track:
                await self.handle_spotify_track(ctx, player, decoded)

            elif decoded["type"] == spotify.SpotifySearchType.playlist:
                await self.handle_spotify_playlist(ctx, player, decoded)

        else:
            node = wavelink.NodePool.get_node()

            tracks = await node.get_tracks(
                cls=wavelink.YouTubeTrack, query=f"ytsearch:{search}"
            )
            embed = discord.Embed(
                title=f"{style.Emoji.REGULAR.music} Select a Song to Play",
                description=f"""```asciidoc
= Showing Song Results for: =
[ {search} ]
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREY,
            )
            selector = PlayerSelector(ctx, node, player, tracks[:25])
            async with self.musicDB.cursor() as cursor:
                await selector.add_recently_played(cursor)
            await ctx.reply(embed=embed, view=selector)

    @commands.hybrid_command(
        name="queue",
        description="""View the current queue for the server""",
        help="""Show what's currently in the players queue!""",
        brief="View Player Queue",
        aliases=["q"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.channel)
    async def queue_cmd(self, ctx: commands.Context) -> None:
        """
        View player queue
        """
        player = await self.get_player(ctx)

        if not player.track:
            raise NothingPlaying()

        if player.queue.is_empty:
            raise QueueEmpty()

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
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="now",
        description="""Show what songs currently being played""",
        help="""Show whats currently being played by Benny""",
        brief="""Now Playing""",
        aliases=["nowplaying", "np"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 5.0, commands.BucketType.channel)
    async def now_cmd(self, ctx: commands.Context) -> None:
        """
        Showing whats now playing
        """
        player = await self.get_player(ctx)

        if not player.is_playing():
            raise NothingPlaying

        current = player.track

        embed = discord.Embed(
            title="Now Playing",
            description=f"""```asciidoc
[ {current.title} ]
= Duration: {duration(current.length)} =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.ORANGE,
        )
        embed.set_author(name=f"Queued by {current.author}")
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="skip",
        description="""Skip the currently playing song""",
        help="""Skip the currently playing song""",
        brief="Skip the currently playing song",
        aliases=["s"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 5.0, commands.BucketType.user)
    async def skip_cmd(self, ctx: commands.Context) -> None:
        """
        Skip command
        """
        player = await self.get_player(ctx)

        current = player.track
        await player.skip()
        embed = discord.Embed(
            title="Skipped",
            url=current.uri,
            description=f"""```asciidoc
[ {current.title} ]
= Duration: {duration(current.length)} =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.ORANGE,
        )
        embed.set_author(name=current.author)
        await ctx.reply(embed=embed)

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
        """
        Disconnect the bot from the voice channel
        """
        player = await self.get_player(ctx)

        await player.disconnect()

        embed = discord.Embed(
            title="Disconnected",
            description=f"""Disconnected from {player.channel.mention}""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.RED,
        )
        await ctx.reply(embed=embed)

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
    async def remove_cmd(self, ctx: commands.Context, *, number: int) -> None:
        """
        Will support removing by song name / author soon.
        """
        player = await self.get_player(ctx)

        index = number - 1

        song = player.queue._queue[index]

        embed = discord.Embed(
            title="Removed",
            url=song.uri,
            description=f"""```asciidoc
[ {song.title} ]
= Duration: {duration(song.length)} =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.RED,
        )
        embed.set_author(name=song.author)
        await ctx.reply(embed=embed)
        del player.queue._queue[index]

    @commands.hybrid_command(
        name="shuffle",
        description="""Shuffle the entire queue""",
        help="""Shuffle the entire queue""",
        brief="Shuffle the queue",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def shuffle_cmd(self, ctx: commands.Context) -> None:
        """
        Shuffle the queue
        """
        player = await self.get_player(ctx)

        current = player.track
        await player.shuffle()
        embed = discord.Embed(
            title=f"{style.Emoji.REGULAR.shuffle} Shuffling",
            url=current.uri,
            description=f"""Shuffled {len(player.queue._queue)} songs""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.YELLOW,
        )
        await ctx.reply(embed=embed)

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
        """
        Looping command
        """
        player = await self.get_player(ctx)

        current = player.track
        await player.loop()
        embed = discord.Embed(
            title=f"{style.Emoji.REGULAR.loop} {'Looping' if player.loop else 'Unlooping'}",
            url=current.uri,
            description=f"""{'Looped' if player.loop else 'Unlooped'} the queue""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="pause",
        description="""Pause the current song""",
        help="""Pause the current song""",
        brief="Pause the current song",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def pause_cmd(self, ctx: commands.Context) -> None:
        """
        Pause the queue
        """
        player = await self.get_player(ctx)

        if player.is_paused:
            raise commands.BadArgument("The player is already paused.")

        await player.set_pause(True)
        embed = discord.Embed(
            title="Paused",
            description="""Paused the queue""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="unpause",
        description="""Unpause the current song""",
        help="""Unpause the current song""",
        brief="Unpause the current song",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def unpause_cmd(self, ctx: commands.Context) -> None:
        """
        Unause the queue
        """
        player = await self.get_player(ctx)

        if player.is_paused:
            await player.set_pause(False)
            embed = discord.Embed(
                title="Unpaused",
                description="""Unpaused the queue""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREEN,
            )
            await ctx.reply(embed=embed)
        else:
            raise commands.BadArgument("The player isn't paused!")

    @commands.hybrid_group(
        name="filter",
        description="""Add different filters to the currently playing song""",
        help="""Add different filters to the currently playing song""",
        brief="Add different filters to the currently playing song",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def filter_group(self, ctx: commands.Context) -> None:
        """
        Add different filters to the currently playing song
        """
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @filter_group.command(
        name="reset",
        description="""Remove all filters and reset""",
        help="""Remove all filters and reset""",
        brief="Remove all filters and reset",
        aliases=["r"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def filter_reset_cmd(self, ctx: commands.Context) -> None:
        """
        Remove all filters and reset
        """
        player = await self.get_player(ctx)

        await player.set_filter(wavelink.Filter(), seek=True)

        embed = discord.Embed(
            title="Success",
            description="""Successfully removed all filters!""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        await ctx.send(embed=embed)

    @filter_group.group(
        name="equalizer",
        description="""Set an equalizer, provides 4 different types""",
        help="""Set an equalizer, provides 4 different types""",
        brief="Set an equalizer, provides 4 different types",
        aliases=["eq"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def filter_equalizer_group(self, ctx: commands.Context) -> None:
        """
        Equalizer filter
        """
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @filter_equalizer_group.command(
        name="boost",
        description="""Equalizer boost filter""",
        help="""Equalizer boost filter""",
        brief="Equalizer boost filter",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    async def filter_equalizer_boost_cmd(self, ctx: commands.Context) -> None:
        """
        Boost Equalizer
        """
        player = await self.get_player(ctx)

        boost = wavelink.Equalizer.boost()

        await player.set_filter(wavelink.Filter(equalizer=boost), seek=True)

        embed = discord.Embed(
            title="Set Boost Equalizer",
            description="""Successfully set a boost equalizer""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        await ctx.reply(embed=embed)

    @filter_group.command(
        name="karaoke",
        description="""Karaoke filter""",
        help="""Karaoke filter""",
        brief="Karaoke",
        aliases=["sing"],
        enabled=True,
        hidden=False,
    )
    async def filter_karaoke_cmd(self, ctx: commands.Context) -> None:
        """
        karaoke filter
        """
        player = await self.get_player(ctx)

        karaoke = wavelink.Karaoke(level=5.0)

        await player.set_filter(wavelink.Filter(karaoke=karaoke), seek=True)

        embed = discord.Embed(
            title="Karaoke Mode Enabled",
            description="""Successfully set track to Karaoke mode""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.PINK,
        )
        await ctx.reply(embed=embed)

    @filter_group.command(
        name="spin",
        description="""Rotate 3d audio filter""",
        help="""Rotate 3d audio filter""",
        brief="Rotate 3d audio filter",
        aliases=["rotate", "3d"],
        enabled=True,
        hidden=False,
    )
    async def filter_spin_cmd(self, ctx: commands.Context) -> None:
        """
        Spinning filter
        """
        player = await self.get_player(ctx)

        embed = discord.Embed(
            title="Spin Mode",
            description="""Set a spin mode below!

            Note the max values of this are 5 and -5, don't get too dizzy!""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.PURPLE,
        )
        await ctx.reply(embed=embed, view=FilterSpinView(ctx, player))

    @commands.hybrid_command(
        name="musescore",
        description="""Get sheet music from musescore""",
        help="""Get sheet music from musescore""",
        brief="Get sheet music from musescore",
        aliases=["sheet", "sheets"],
        enabled=False,
        hidden=False,
    )
    @commands.cooldown(1.0, 10.0, commands.BucketType.default)
    async def musescore_cmd(self, ctx: commands.Context, *, search: str) -> None:
        """
        Get sheet music from musescore
        """
        await ctx.defer()
        async with MuseScraper() as ms:
            url = urlparse(search)

            if url.scheme == "https" and url.netloc == "musescore.com":
                if url.hostname == "musescore.com":
                    embed = discord.Embed(
                        title="Downloading...",
                        timestamp=discord.utils.utcnow(),
                        color=style.Color.GREY,
                    )
                    message = await ctx.reply(embed=embed)
                    path = await ms.download(search, "Musescore/")
                    file = discord.File(path)

                    embed = discord.Embed(
                        title="Downloaded Successfully",
                        timestamp=discord.utils.utcnow(),
                        color=style.Color.GREEN,
                    )
                    await message.edit(embed=embed)
                    await ctx.send(file=file)
                    await self.bot.loop.run_in_executor(os.remove, path)
                else:
                    raise commands.BadArgument("Invalid URL")
            else:
                raise commands.BadArgument("Invalid URL")


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Music(bot))
