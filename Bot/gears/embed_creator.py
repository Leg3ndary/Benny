"""
An Embed Creator
"""

import discord
import style
from discord.ext import commands


class EmbedModal(discord.ui.Modal):
    """
    Embed Modal to edit a field
    """

    def __init__(self, _property: str) -> None:
        """
        Init the modal
        """
        super().__init__()
        self._property = _property
        self.add_item(
            discord.ui.TextInput(
                label=_property,
                style=discord.TextStyle.long,
                placeholder="Add something here!",
                max_length=4000,
                min_length=1,
                required=True,
            )
        )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        On_submit, do stuff
        """


class EmbedDropdown(discord.ui.Select):
    """
    A Select for editing embeds
    """

    def __init__(self, embed: discord.Embed) -> None:
        """
        Init the embed creation select
        """
        self.embed = embed

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
            "Title": embed.title if embed.title else "None",
            "URL": embed.url if embed.url else "None",
            "Description": embed.description if embed.description else "None",
            "Fields": embed.fields if embed.fields else "None",
            "Image": embed.image if embed.image else "None",
            "Thumbnail": embed.thumbnail if embed.thumbnail else "None",
            "Footer Text": embed.footer.text
            if embed.footer and embed.footer.text
            else "None",
            "Footer Icon": embed.footer.icon_url
            if embed.footer and embed.footer.icon_url
            else "None",
            "Timestamp": embed.timestamp if embed.timestamp else "None",
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
            placeholder="Choose a property to Edit",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """
        Select a field to edit
        """
        meaning = self.meanings[int(self.values[0])]

        embed = discord.Embed(
            title=f"{self.word.word} Definition",
            url=self.word.phonetics[0].audio if self.word.phonetics[0].audio else None,
            timestamp=discord.utils.utcnow(),
            color=style.Color.MAROON,
        )
        embed.add_field(
            name="Part of Speech", value=meaning.part_of_speech, inline=False
        )
        embed.add_field(
            name="Definition",
            value=f"{meaning.definitions[0].definition}\n>>> {meaning.definitions[0].example if meaning.definitions[0].example else 'No Example'}",
            inline=False,
        )
        embed.set_author(
            name=f"License: {self.word.license.name}",
            url=self.word.license.url,
        )
        embed.set_footer(
            text=f"Meaning {int(self.values[0]) + 1}/{len(self.word.meanings)}"
        )
        await interaction.response.edit_message(embed=embed, view=self.view)


class EmbedView(discord.ui.View):
    """
    Embed view for storing the embed editor
    """

    def __init__(self, ctx: commands.Context) -> None:
        """
        Create the embed view
        """
        self.ctx = ctx
        super().__init__()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        If the interaction isn't by the user, return a fail.
        """
        if interaction.user != self.ctx.author:
            return False
        return True

    @discord.ui.button(label="button", style=discord.ButtonStyle.blurple)
    async def add_field_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Add a field
        """
