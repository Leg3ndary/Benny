import asyncio
import discord
import discord.utils
from discord.ext import commands
import discord.app_commands as app_commands
from gears import style
import googletrans


class gm_Translated:
    """
    Empty Model because for some reason googletrans didn't make models part of the package?
    """

    def __init__(self, src: str, dest: str, origin: str, text: str, pronunciation: str, extra_data=None, **kwargs) -> None:
        """
        Empty Model
        """
        super().__init__(**kwargs)
        self.src = src
        self.dest = dest
        self.origin = origin
        self.text = text
        self.pronunciation = pronunciation
        self.extra_data = extra_data


class gm_Detected:
    """Empty model for language detection"""

    def __init__(self, lang: str, confidence: float, **kwargs) -> None:
        """
        Empty Model
        """
        super().__init__(**kwargs)
        self.lang = lang
        self.confidence = confidence


class Translator:
    """
    Custom class to provide async translate responses and more stuff
    """

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Init with stuff we need mmhm
        """
        self.loop = loop
        self.translator = googletrans.Translator()

    async def translate(self, text: str) -> gm_Translated:
        """
        Translate text with an asynchronously
        """
        result = await self.loop.run_in_executor(None, self.translator.translate, text)
        return result

    async def detect(self, text: str) -> gm_Detected:
        """
        Detect language asynchronously
        """
        result = await self.loop.run_in_executor(None, self.translator.detect, text)
        return result

    async def process(self, channel: discord.TextChannel, text: str) -> None:
        """
        Process a translation
        """

        translated = await self.translate(text)

        embed = discord.Embed(
            title=f"Translating Text",
            timestamp=discord.utils.utcnow(),
            color=style.Color.PINK
        )
        embed.add_field(
            name=f"Original: {googletrans.LANGUAGES.get(translated.src).capitalize()}",
            value=translated.origin[:1000]
        )
        embed.add_field(
            name=f"Translated: {googletrans.LANGUAGES.get(translated.dest).capitalize()}",
            value=translated.text[:1000]
        )

        view = TranslateView(translated)

        await channel.send(embed=embed, view=view)


class TranslateView(discord.ui.View):
    """
    TranslateView that shows a few more options
    """

    def __init__(self, translated: gm_Translated) -> None:
        """Init"""
        super().__init__()
        self.translated = translated

    @discord.ui.button(label="Original", style=discord.ButtonStyle.grey)
    async def original_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show the original translation and related info"""
        embed = discord.Embed(
            title=f"Original: {googletrans.LANGUAGES.get(self.translated.src).capitalize()}",
            description=self.translated.origin[:4000],
            timestamp=discord.utils.utcnow(),
            color=style.Color.PINK
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Translated", style=discord.ButtonStyle.green)
    async def translated_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show the translated translation and related info"""
        embed = discord.Embed(
            title=f"Translated: {googletrans.LANGUAGES.get(self.translated.dest).capitalize()}",
            description=self.translated.text[:4000],
            timestamp=discord.utils.utcnow(),
            color=style.Color.PINK
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class Translate(commands.Cog):
    """Everything to do with translating"""

    def __init__(self, bot: commands.Bot) -> None:
        """Init the translate cog"""
        self.bot = bot
        self.translator = Translator(bot.loop)
        self.translate_menu = app_commands.ContextMenu(
            name="Translate",
            callback=self.translate_context_menu
        )
        self.bot.tree.add_command(self.translate_menu)

    async def cog_unload(self) -> None:
        """
        On cog unload remove the menu
        """
        self.bot.tree.remove_command(self.translate_menu.name, type=self.translate_menu.type)

    @commands.hybrid_command(
        name="translate",
        description="""Translate the text given into english""",
        help="""Translate the given text into the english language""",
        brief="Translate the given text into english",
        aliases=["trans"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def translate_cmd(self, ctx: commands.Context, *, text: str) -> None:
        """Translate text"""
        await self.translator.process(ctx.channel, text)

    async def translate_context_menu(self, interaction: discord.Interaction, msg: discord.Message) -> None:
        """
        Translate context menu
        """
        await self.translator.process(msg.channel, msg.content)
        

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Translate(bot))