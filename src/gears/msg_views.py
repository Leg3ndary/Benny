import discord
from gears.style import c_get_emoji, c_get_color

class DeleteView(discord.ui.View):
    """Delete view to delete the message from the bot"""
    def __init__(self, slash: bool=False):
        """ctx: The context object needed to delete the original message"""
        self.bctx = None
        self.slash = slash
        super().__init__()

    @discord.ui.button(
        emoji="🗑️",
        label="A button",
        style=discord.ButtonStyle.danger
    )
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

    @discord.ui.button(emoji=await c_get_emoji("regular", "loop"), label="", style=discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        self.player.set_repeat(not self.is_repeat)
        if not self.is_repeat:
            repeat = "Unloop"
        else:
            repeat = "Loop"
        button.label = repeat
        await interaction.response.edit_message(view=self)
        embed = discord.Embed(
            title=f"""{await c_get_emoji("regular", "loop")} {repeat}ing""",
            description=f"""{repeat}ing the current queue""",
            timestamp=discord.utils.utcnow(),
            color=await c_get_color("aqua"),
        )
        if not self.slash:
            await self.bctx.edit(embed=embed)
        else:
            await self.bctx.delete_original_message(embed=embed)