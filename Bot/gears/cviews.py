import discord
import json
import lavalink
from gears import style, util


config = json.load(open("config.json"))

if config["Lavalink"]["Search"] == "ytsearch":
    PlayerDropdownEmoji = style.get_emoji("regular", "youtube")
else:
    PlayerDropdownEmoji = style.get_emoji("regular", "soundcloud")


class DeleteView(discord.ui.View):
    """Delete view to delete the message from the bot"""

    def __init__(self, slash: bool = False):
        """ctx: The context object needed to delete the original message"""
        self.bctx = None
        self.slash = slash
        super().__init__()

    @discord.ui.button(emoji="🗑️", label="Delete", style=discord.ButtonStyle.danger)
    async def button_callback(self, button, interaction):
        if not self.slash:
            await self.bctx.delete()
        else:
            await self.bctx.delete_original_message()
        await interaction.response.send_message("Message Deleted", ephemeral=True)


class LoopButton(discord.ui.View):
    """Loop or unloop the queue when this button's pressed"""

    def __init__(self, slash, is_repeat: bool, player):
        self.bctx = None
        self.slash = slash
        self.player = player
        self.is_repeat = is_repeat

        super().__init__()

    @discord.ui.button(
        emoji=style.get_emoji("regular", "loop"),
        label="",
        style=discord.ButtonStyle.primary,
    )
    async def button_callback(self, button, interaction):
        self.player.set_repeat(not self.is_repeat)
        if not self.is_repeat:
            repeat = "Unloop"
        else:
            repeat = "Loop"
        button.label = repeat
        await interaction.response.edit_message(view=self)
        embed = discord.Embed(
            title=f"""{style.get_emoji("regular", "loop")} {repeat}ing""",
            description=f"""{repeat}ing the current queue""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("aqua"),
        )
        if not self.slash:
            await self.bctx.edit(embed=embed)
        else:
            await self.bctx.delete_original_message(embed=embed)


class PlayerManagerView(discord.ui.View):
    """View to manage player from a specific guild (not done)"""

    def __init__(self, player):
        self.player = player
        super().__init__()

    @discord.ui.select(
        placeholder="Select song info",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="Song Name", description="Artist and duration", emoji="🟥"
            ),
            discord.SelectOption(
                label="Song Name 2", description="selected song 2", emoji="🟩"
            ),
            discord.SelectOption(
                label="Song3", description="seleceted song 3", emoji="🟦"
            ),
        ],
    )
    async def select_callback(self, select, interaction):
        await interaction.response.send_message(
            f"You selected {select.values[0]}", ephemeral=True
        )

    @discord.ui.button(
        emoji=style.get_emoji("regular", "loop"), style=discord.ButtonStyle.green
    )
    async def loop_callback(self, button, interaction):
        await interaction.response.send_message(
            "pretend this was looped", ephemeral=True
        )

    @discord.ui.button(
        emoji=style.get_emoji("regular", "left"), style=discord.ButtonStyle.grey
    )
    async def left_callback(self, button, interaction):
        await interaction.response.send_message(
            "pretend this was rewinded to the start", ephemeral=True
        )

    @discord.ui.button(
        emoji=style.get_emoji("regular", "stop"), style=discord.ButtonStyle.red
    )
    async def stop_callback(self, button, interaction):
        await interaction.response.send_message(
            "pretend this was stopped", ephemeral=True
        )

    @discord.ui.button(
        emoji=style.get_emoji("regular", "right"), style=discord.ButtonStyle.grey
    )
    async def right_callback(self, button, interaction):
        await interaction.response.send_message(
            "pretend this was skipped and moved to the right", ephemeral=True
        )

    @discord.ui.button(
        emoji=style.get_emoji("regular", "search"), style=discord.ButtonStyle.blurple
    )
    async def search_callback(self, button, interaction):
        await interaction.response.send_message(
            "pretend you can now search for something", ephemeral=True
        )


class PlayerDropdown(discord.ui.Select):
    """Shows up to 25 songs in a select"""

    def __init__(self, ctx, player, songs: list):
        self.ctx = ctx
        self.player = player
        self.songs = songs
        options = []
        counter = 0
        for song in songs:
            options.append(
                discord.SelectOption(
                    emoji=PlayerDropdownEmoji,
                    label=song["info"]["title"],
                    description=f"""{song["info"]["author"]} - Duration: {util.remove_zcs(lavalink.format_time(song["info"]["length"]))}""",
                    value=str(counter),
                )
            )
            counter += 1

        super().__init__(
            placeholder="Select a Song", min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        track = self.songs[int(self.values[0])]

        embed = discord.Embed(
            title=f"Track Queued",
            url=track["info"]["uri"],
            description=f"""```asciidoc
[ {track["info"]["title"]} ]
= Duration: {util.remove_zcs(lavalink.format_time(track["info"]["length"]))} =
```""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("green"),
        )
        embed.set_author(name=track["info"]["author"])
        embed.set_footer(
            text=self.ctx.author.display_name,
            icon_url=self.ctx.author.display_avatar.url,
        )

        track = lavalink.models.AudioTrack(track, self.ctx.author.id, recommended=True)
        self.player.add(requester=self.ctx.author.id, track=track)
        await interaction.response.edit_message(embed=embed, view=None)

        # We don't want to call .play() if the player is playing as that will effectively skip the current track.
        if not self.player.is_playing:
            await self.player.play()

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


class QueueClear(discord.ui.View):
    """Clear the queue?"""

    def __init__(self, ctx, queue):
        self.ctx = ctx
        self.queue = queue
        self.embed = None
        super().__init__()

    async def interaction_check(self, interaction):
        """If the interaction isn't by the user, return a fail."""
        if interaction.user != self.ctx.author:
            return False
        return True

    @discord.ui.button(
        emoji=style.get_emoji("regular", "check"),
        label="Confirm",
        style=discord.ButtonStyle.green,
    )
    async def confirm_callback(self, button, interaction):
        """Delete the message if clicked"""
        embed = discord.Embed(
            title=f"Confirmed",
            description=f"""The queue has been cleared""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("green"),
        )
        for item in self.children:
            item.disabled = True
        await self.embed.edit(embed=embed, view=self)
        self.queue.clear()

    @discord.ui.button(
        emoji=style.get_emoji("regular", "cancel"),
        label="Cancel",
        style=discord.ButtonStyle.danger,
    )
    async def cancel_callback(self, button, interaction):
        """Edit the message if clicked"""
        embed = discord.Embed(
            title=f"Cancelled",
            description=f"""Action cancelled""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("red"),
        )
        for item in self.children:
            item.disabled = True
        await self.embed.edit(embed=embed, view=self)


class PlaylistViewer(discord.ui.View):
    """Clear the queue?"""

    def __init__(self, ctx, player, playlistdb):
        self.ctx = ctx
        self.player = player
        self.playlistdb = playlistdb
        self.embed = None
        super().__init__()

    async def interaction_check(self, interaction):
        """If the interaction isn't by the user, return a fail."""
        if interaction.user != self.ctx.author:
            return False
        return True

    @discord.ui.button(
        emoji=style.get_emoji("regular", "cancel"),
        label="Close",
        style=discord.ButtonStyle.danger,
        row=2,
    )
    async def cancel_callback(self, button, interaction):
        """Delete the message if clicked"""
        embed = discord.Embed(
            title=f"Cancelled",
            description=f"""Action cancelled""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("red"),
        )
        for item in self.children:
            item.disabled = True
        await self.embed.edit(embed=embed, view=self)


class QueueView(discord.ui.View):
    """Queue view"""

    def __init__(self, player):
        self.player = player
        self.embed = None
        super().__init__(timeout=60)

    @discord.ui.button(label="Normal", style=discord.ButtonStyle.grey)
    async def normal_button(self, button, interaction):
        """When the user wants to see the normal view"""
        queue = self.player.queue

        if not queue:
            # Queue is empty
            embed = discord.Embed(
                title=f"Nothing's been Queued!",
                description=f"""Use the play command to queue more songs!""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("aqua"),
            )
            await self.embed.edit(embed=embed)
            self.stop()

        queue_visual = ""

        total_duration = 0
        total_duration += self.player.current.duration

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
        if self.player.repeat:
            lemoji = style.get_emoji("regular", "check")
        else:
            lemoji = style.get_emoji("regular", "cancel")
        if self.player.shuffle:
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
        await self.embed.edit(embed=embed, view=self)

    @discord.ui.button(label="Colorful", style=discord.ButtonStyle.blurple)
    async def colorful_button(self, button, interaction):
        """When the user wants to see the normal view"""
        queue = self.player.queue

        if not queue:
            # Queue is empty
            embed = discord.Embed(
                title=f"Nothing's been Queued!",
                description=f"""Use the play command to queue more songs!""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("aqua"),
            )
            await self.embed.edit(embed=embed)
            self.stop()

        queue_visual = ""

        total_duration = 0
        total_duration += self.player.current.duration

        for count, track in enumerate(queue, 1):
            queue_visual = f"""{queue_visual}\n{util.ansi("WHITE", None, "BOLD")}[{util.ansi("RED", None, "BOLD", "UNDERLINE")} {count} {util.ansi("WHITE", None, "BOLD")}] {util.ansi("BLUE")}{track.title} {util.ansi("WHITE", None, "BOLD")}[{util.ansi("GREEN", None, "UNDERLINE")}{track.author}{util.ansi("WHITE", None, "BOLD")}]{util.ansi("RESET")} ({util.remove_zcs(lavalink.format_time(track.duration))})"""
            total_duration += track.duration

        embed = discord.Embed(
            title=f"Queue - {len(queue)} Tracks",
            description=f"""```ansi
{queue_visual}
```""",
            timestamp=discord.utils.utcnow(),
            color=style.get_color("green"),
        )
        if self.player.repeat:
            lemoji = style.get_emoji("regular", "check")
        else:
            lemoji = style.get_emoji("regular", "cancel")
        if self.player.shuffle:
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
        await self.embed.edit(embed=embed, view=self)
