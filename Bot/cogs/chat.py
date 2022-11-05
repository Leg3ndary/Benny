import io
import time

import aiohttp
import discord
import PIL as pil
import pytesseract
import torch
from discord.ext import commands
from gears import dictapi, style
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

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        If the interaction isn't by the user, return a fail.
        """
        if interaction.user != self.ctx.author:
            return False
        return True

    @discord.ui.button(label="Chat", style=discord.ButtonStyle.primary, emoji="💬")
    async def chat_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """
        Chat button
        """
        await interaction.response.send_modal(self.modal)


class DictDropdown(discord.ui.Select):
    """
    Dict Dropdown
    """

    def __init__(self, word: dictapi.Word) -> None:
        """
        Init the dict dropdown
        """
        self.word = word
        self.meanings = list(word.meanings)[:25]

        options = []

        for counter, meaning in enumerate(self.meanings):
            options.append(
                discord.SelectOption(
                    label=meaning.part_of_speech,
                    description=f"{meaning.definitions[0].definition[:47]}..."
                    if len(meaning.definitions[0].definition) > 50
                    else meaning.definitions[0].definition,
                    value=counter,
                )
            )

        super().__init__(
            placeholder="Choose a Meaning to View",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """
        Select a word to define
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


class DictionaryMenu(discord.ui.View):
    """
    Dictionary Menu
    """

    def __init__(self, ctx: commands.Context, word: dictapi.Word) -> None:
        """
        Initiative it
        """
        super().__init__()
        self.ctx = ctx
        self.add_item(DictDropdown(word))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        If the interaction isn't by the user, return a fail.
        """
        if interaction.user != self.ctx.author:
            return False
        return True


class IMGReader:
    """
    Read images
    """

    __slots__ = ("bot", "loop")

    def __init__(self, bot: commands.Bot) -> None:
        """
        construct the image reader
        """
        self.bot = bot
        self.loop = bot.loop

        if not bot.PLATFORM == "linux":
            pytesseract.pytesseract.tesseract_cmd = (
                "C:/Program Files/Tesseract-OCR/tesseract.exe"
            )

    async def read_img(self, image_bytes: bytes) -> str:
        """
        Read an image and return the text in it

        Parameters
        ----------
        image_bytes: bytes
            Image bytes

        Returns
        -------
        str
            The actual text found
        """

        img = await self.loop.run_in_executor(
            None, pil.Image.open, io.BytesIO(image_bytes)
        )
        text = await self.loop.run_in_executor(
            None, pytesseract.pytesseract.image_to_string, img
        )

        return text


class Chat(commands.Cog):
    """
    Language related commands, AI Chat, dictionary, image reading etc
    """

    COLOR = style.Color.YELLOW
    ICON = "💬"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init the cog
        """
        self.bot = bot
        self.dc: dictapi.DictClient = dictapi.DictClient(bot.sessions.get("main"))
        self.imgr = IMGReader(bot)

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

    @commands.hybrid_command(
        name="define",
        description="""Get a words amazing definition""",
        help="""Define a word""",
        brief="Define a word",
        aliases=["dict", "def"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def define_cmd(self, ctx: commands.Context, *, word: str) -> None:
        """
        Define a word
        """
        if not word.isalpha():
            raise commands.BadArgument(
                "The requested definition must be alphabetic, this means no spaces or special characters"
            )

        data = await self.dc.fetch_word(word)
        status = data.get("status")
        json = data.get("data")

        if status == 200:
            word = dictapi.Word(json[0])

            embed = discord.Embed(
                title=f"{word.word} Definition",
                description="""Select one of the below to view different meanings of the word.""",
                url=(word.phonetics[0].audio if word.phonetics[0].audio else None) if word.phonetics else None,
                timestamp=discord.utils.utcnow(),
                color=style.Color.MAROON,
            )
            embed.set_author(
                name=f"License: {word.license.name}",
                url=word.license.url,
            )
            embed.set_footer(text=f"Meaning -/{len(word.meanings)}")
            await ctx.send(embed=embed, view=DictionaryMenu(ctx, word))

    @commands.hybrid_command(
        name="imgread",
        description="""Read text off an image using a machine learning model""",
        help="""Read text off an image""",
        brief="Read text off an image",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 10.0, commands.BucketType.user)
    async def imgread_cmd(self, ctx: commands.Context, url: str = None) -> None:
        """
        Use pytesseract to read stuff yay.
        """
        if url:
            async with self.session as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    image_bytes = await response.read()

        elif ctx.message.attachments:
            image_bytes = await ctx.message.attachments[0].read()

        else:
            raise commands.BadArgument("Please provide an image or url to read.")

        text = await self.imgr.read_img(image_bytes)

        if len(text) > 2010:
            embed = discord.Embed(
                title="Image Read",
                description=f"""The text was {len(text)} characters, so it was sent as a file.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.PURPLE,
            )
            await ctx.reply(
                embed=embed,
                file=discord.File(io.StringIO(text), f"imgread-{int(time.time())}.txt"),
            )
        else:
            embed = discord.Embed(
                title="Image Read",
                description=f"""```
{text}
```""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.PURPLE,
            )
            await ctx.reply(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """
    Setup the cog.
    """
    await bot.add_cog(Chat(bot))
