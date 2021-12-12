import discord

class DeleteView(discord.ui.View):
    """Delete view to delete the message from the bot"""
    def __init__(self, slash: bool=False):
        """ctx: The context object needed to delete the original message"""
        self.bctx = None
        self.slash = slash
        super().__init__()

    @discord.ui.button(
        label="A button",
        emoji="🗑️",
        style=discord.ButtonStyle.danger
    )
    async def button_callback(self, button, interaction):
        if not self.slash:
            await self.bctx.delete()
        else:
            await self.bctx.delete_original_message()
        await interaction.response.send_message("Message Deleted", ephemeral=True)