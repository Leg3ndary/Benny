"""
An Embed Creator
"""

import io
import json

import discord
import mystbin
from discord.ext import commands

from . import style


class CustomEmbedPropertyModal(discord.ui.Modal):
    """
    Embed Modal to edit a field
    """

    def __init__(self, select: discord.ui.Select) -> None:
        """
        Init the modal
        """
        super().__init__(title=select.values[0])
        self.select = select
        params = {
            "Author Name": "The text in the upper part of the embed",
            "Author URL": "The URL for the upper part of the embed",
            "Author Icon": "The URL for the icon in the upper part of the embed",
            "Color": "The color of the embed",
            "Title": "The title of the embed",
            "Description": "The description of the embed",
            "Fields": "Add something here",
            "Image": "The URL for the image in the embed",
            "Thumbnail": "The URL for the thumbnail in the embed",
            "Footer Text": "The footer text of the embed",
            "Footer Icon": "The URL for the icon in the footer of the embed",
            "Timestamp": "The timestamp of the embed",
        }
        self.added_property = discord.ui.TextInput(
            label=select.values[0],
            style=discord.TextStyle.long,
            placeholder=params[select.values[0]],
            max_length=4000,
            min_length=1,
            required=True,
        )
        self.add_item(self.added_property)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        On_submit, do stuff
        """
        embed: discord.Embed = self.select.view.embed
        if self.added_property.value == "Author Name":
            embed.set_author(
                name=self.added_property.value,
                url=embed.author.url,
                icon_url=embed.author.icon_url,
            )
        elif self.added_property.value == "Author URL":
            embed.set_author(
                name=embed.author.name,
                url=self.added_property.value,
                icon_url=embed.author.icon_url,
            )
        elif self.added_property.value == "Author Icon":
            embed.set_author(
                name=embed.author.name,
                url=embed.author.url,
                icon_url=self.added_property.value,
            )
        elif self.added_property.value == "Color":
            embed.color = self.added_property.value
        elif self.added_property.value == "Title":
            embed.title = self.added_property.value
        elif self.added_property.value == "Description":
            embed.description = self.added_property.value
        elif self.added_property.value == "Fields":
            pass
        elif self.added_property.value == "Image":
            embed.set_image(url=self.added_property.value)
        elif self.added_property.value == "Thumbnail":
            embed.set_thumbnail(url=self.added_property.value)
        elif self.added_property.value == "Footer Text":
            embed.set_footer(
                text=self.added_property.value, icon_url=embed.footer.icon_url
            )
        elif self.added_property.value == "Footer Icon":
            embed.set_footer(text=embed.footer.text, icon_url=self.added_property.value)
        elif self.added_property.value == "Timestamp":
            embed.timestamp = self.added_property.value
        await interaction.response.edit_message(embed=embed, view=self.select.view)


class CustomEmbedImportModal(discord.ui.Modal, title="Import Embed"):
    """
    Import Modal to import a field
    """

    import_link = discord.ui.TextInput(
        label="Import Link",
        style=discord.TextStyle.long,
        placeholder="https://mystb.in/SomeRandomID",
        max_length=4000,
        min_length=1,
        required=True,
    )

    def __init__(self, view: discord.ui.View) -> None:
        """
        Init the modal
        """
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        On_submit, do stuff
        """
        if self.import_link.value.startswith("https://mystb.in/"):
            paste: mystbin.Paste = await self.view.ctx.bot.mystbin.get_paste(
                self.import_link.value.replace("https://mystb.in/", "")
            )
            if paste.files[0].filename.endswith(".json"):
                full_json = json.loads(paste.files[0].content)
                self.view.embed = discord.Embed.from_dict(full_json)
                await interaction.response.edit_message(
                    embed=self.view.embed, view=self.view
                )
            else:
                embed = discord.Embed(
                    title="Error",
                    description="""The file in the mystbin doesn't end with `.json`""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.RED,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="Error",
                description="""This link doesn't seem to be a valid https://mystb.in/ link!""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


class CustomEmbedSendModal(discord.ui.Modal, title="Send Embed"):
    """
    Send Modal to send embed to a different or same channel
    """

    channel_input = discord.ui.TextInput(
        label="Channel",
        style=discord.TextStyle.long,
        placeholder="Channel ID",
        max_length=4000,
        min_length=1,
        required=True,
    )

    def __init__(self, view: discord.ui.View) -> None:
        """
        Init the modal
        """
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        On_submit, do stuff
        """
        channel: discord.TextChannel = self.view.ctx.bot.get_channel(
            int(self.channel_input.value)
        ) or await self.view.ctx.bot.fetch_channel(int(self.channel_input.value))

        if channel:
            if channel.permissions_for(self.view.ctx.me).send_messages:
                await channel.send(embed=self.view.embed)
                embed = discord.Embed(
                    title="Sent Embed",
                    description="""Sent successfully!""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.GREEN,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="Error",
                    description="""I don't have permissions to send messages in that channel!""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.RED,
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="Error",
                description="""This channel doesn't exist!""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


class CustomEmbedDropdown(discord.ui.Select):
    """
    A Select for editing embeds
    """

    def __init__(self, embed: discord.Embed) -> None:
        """
        Init the embed creation select
        """

        options = []

        params = {
            "Author Name": embed.author.name
            if embed.author and embed.author.name
            else "None",
            "Author URL": embed.author.url
            if embed.author and embed.author.url
            else "None",
            "Author Icon": embed.author.icon_url
            if embed.author and embed.author.icon_url
            else "None",
            "Color": embed.color if embed.color else "0",
            "Title": embed.title if embed.title else "None",
            "URL": embed.url if embed.url else "None",
            "Description": embed.description if embed.description else "None",
            "Fields": f"{len(embed.fields)} field(s)" if embed.fields else "None",
            "Image": embed.image if embed.image else "None",
            "Thumbnail": embed.thumbnail if embed.thumbnail else "None",
            "Footer Text": embed.footer.text
            if embed.footer and embed.footer.text
            else "None",
            "Footer Icon": embed.footer.icon_url
            if embed.footer and embed.footer.icon_url
            else "None",
            "Timestamp": str(embed.timestamp.timestamp())
            if embed.timestamp
            else "None",
        }

        for key, value in params.items():
            options.append(
                discord.SelectOption(
                    label=key,
                    description=f"{value[:47]}..." if len(value) > 50 else value,
                    value=key,
                )
            )

        super().__init__(
            placeholder="Choose a Property to Edit",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """
        Select a Property to edit
        """
        await interaction.response.send_modal(CustomEmbedPropertyModal(self))


class CustomEmbedView(discord.ui.View):
    """
    Embed view for storing the embed editor
    """

    def __init__(self, ctx: commands.Context) -> None:
        """
        Create the embed view
        """
        super().__init__()
        self.ctx = ctx
        self.embed: discord.Embed = discord.Embed(
            title="Embed Creator",
            description="Create an embed with this view!",
            timestamp=discord.utils.utcnow(),
        )
        self.add_item(CustomEmbedDropdown(self.embed))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        If the interaction isn't by the user, return a fail.
        """
        if interaction.user != self.ctx.author:
            return False
        return True

    @discord.ui.button(label="Import", style=discord.ButtonStyle.blurple, emoji="📥")
    async def import_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Import an embed
        """
        await interaction.response.send_modal(CustomEmbedImportModal(self))

    @discord.ui.button(label="Export", style=discord.ButtonStyle.blurple, emoji="📤")
    async def export_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Export an embed
        """
        file = discord.File(
            io.StringIO(json.dumps(self.embed.to_dict())), "custom_embed.json"
        )
        embed = discord.Embed(
            title="Exported Successfully",
            description="""Exported your embed successfully.""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        await interaction.response.send_message(embed=embed, file=file)

    @discord.ui.button(label="Send", style=discord.ButtonStyle.green, emoji="💬")
    async def send_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Send the embed to a channel
        """
        await interaction.response.send_modal(CustomEmbedSendModal(self))

    @discord.ui.button(
        label="Add Field",
        style=discord.ButtonStyle.green,
        emoji=style.Emoji.REGULAR.check,
        row=3,
    )
    async def add_field_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Add a field
        """

    @discord.ui.button(
        label="Remove Field",
        style=discord.ButtonStyle.red,
        emoji=style.Emoji.REGULAR.cancel,
        row=3,
    )
    async def remove_field_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Remove a field
        """
