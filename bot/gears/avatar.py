import discord

from . import style


class AvatarView(discord.ui.View):
    """
    Delete view to delete the message from the interactions response
    """

    @discord.ui.button(
        emoji=style.Emoji.REGULAR.cancel,
        label="Delete",
        style=discord.ButtonStyle.danger,
    )
    async def button_callback(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Delete the message
        """
        await interaction.message.delete()
