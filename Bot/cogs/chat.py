import traceback

import discord
import torch
from discord.ext import commands
from gears import style
from transformers import AutoModelForCausalLM, AutoTokenizer

tokenizer: AutoTokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
model: AutoModelForCausalLM = AutoModelForCausalLM.from_pretrained(
    "Assets/MichaelScott/"
)


class ChatModal(discord.ui.Modal, title="Chat"):
    """
    A Chat Modal so our user can continuously chat with Michael Scott.
    """

    name = discord.ui.TextInput(
        label="Chat",
        style=discord.TextStyle.long,
        placeholder="Hello there!",
        max_length=750,
        min_length=10,
        required=True,
    )

    def __init__(self) -> None:
        """
        Init the modal
        """
        super().__init__()
        self.step = 0
        self.convo = []
        self.chat_history_ids = None

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        On_submit, do stuff
        """
        new_user_input_ids = tokenizer.encode(
            self.name.value + tokenizer.eos_token, return_tensors="pt"
        )

        bot_input_ids = (
            torch.cat(
                [self.chat_history_ids, new_user_input_ids],
                dim=-1,  # pylint: disable=used-before-assignment
            )
            if self.step > 0
            else new_user_input_ids
        )

        self.chat_history_ids = model.generate(
            bot_input_ids,
            max_length=200,
            pad_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=3,
            do_sample=True,
            top_k=100,
            top_p=0.7,
            temperature=0.8,
        )
        response = tokenizer.decode(
            self.chat_history_ids[:, bot_input_ids.shape[-1] :][0],
            skip_special_tokens=True,
        )
        self.convo.append(f"{interaction.user.name}: {self.name.value}")
        self.convo.append(f"Michael: {response}")
        full_convo = "\n".join(self.convo)
        embed = discord.Embed(
            title="Chat with Michael Scott",
            description=f"""```yaml
{full_convo}
{interaction.user.name}:
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREY,
        )
        self.step += 1

        await interaction.response.edit_message(embed=embed)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        """
        When stuff goes wrong lol
        """
        await interaction.response.send_message(
            "Oops! Something went wrong.", ephemeral=True
        )
        traceback.print_tb(error.__traceback__)


class ChatView(discord.ui.View):
    """
    Chat view
    """

    def __init__(self) -> None:
        """
        Init the Chat View
        """
        super().__init__()
        self.modal = ChatModal()

    @discord.ui.button(label="Chat", style=discord.ButtonStyle.primary, emoji="💬")
    async def chat_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """
        Chat button
        """
        await interaction.response.send_modal(self.modal)


class Chat(commands.Cog):
    """
    This cog allows you to chat with our own ai bot
    """

    COLOR = style.Color.YELLOW
    ICON = "💬"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init the cog
        """
        self.bot = bot

    @commands.hybrid_command(
        name="chat",
        description="""Chat with AI""",
        help="""This ai is trained on Michael Scott's quotes and responds to them""",
        brief="Chat with a pretrained AI",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def chat_cmd(self, ctx: commands.Context) -> None:
        """
        Chat with the bot
        """
        await ctx.defer()
        view = ChatView()

        embed = discord.Embed(
            title="Chat with Michael Scott",
            description=f"""```yaml
{ctx.author.name}: 
```""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREY,
        )
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    """
    Setup the cog.
    """
    await bot.add_cog(Chat(bot))
