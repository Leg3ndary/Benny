from typing import Union

import aiogtrans
import discord
import discord.app_commands as app_commands
import discord.utils
from discord.ext import commands
from gears import style


class Translator:
    """
    Custom class to provide async translate responses and more stuff
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init with stuff we need mmhm
        """
        self.translator = aiogtrans.AiohttpTranslator(
            bot.loop, bot.sessions.get("translate")
        )

    async def process(
        self,
        method: Union[commands.Context, discord.Interaction, discord.Message],
        text: str,
    ) -> None:
        """
        Process a translation
        """

        translated = await self.translator.translate(text)

        embed = discord.Embed(
            title="Translating Text",
            timestamp=discord.utils.utcnow(),
            color=style.Color.PINK,
        )
        embed.add_field(
            name=f"Original: {aiogtrans.LANGUAGES.get(translated.src).capitalize()}",
            value=translated.origin[:1000],
        )
        embed.add_field(
            name=f"Translated: {aiogtrans.LANGUAGES.get(translated.dest).capitalize()}",
            value=translated.text[:1000],
        )

        view = TranslateView(translated)

        if isinstance(method, commands.Context):
            await method.reply(embed=embed, view=view)
        elif isinstance(method, discord.Interaction):
            await method.response.send_message(embed=embed, view=view)
        elif isinstance(method, discord.Message):
            await method.reply(embed=embed, view=view)


class TranslateView(discord.ui.View):
    """
    TranslateView that shows a few more options
    """

    def __init__(self, translated: aiogtrans.Translated) -> None:
        """
        Construct the translate view
        """
        super().__init__()
        self.translated = translated

    @discord.ui.button(label="Original", style=discord.ButtonStyle.grey)
    async def original_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """
        Show the original translation and related info
        """
        embed = discord.Embed(
            title=f"Original: {aiogtrans.LANGUAGES.get(self.translated.src).capitalize()}",
            description=self.translated.origin[:4000],
            timestamp=discord.utils.utcnow(),
            color=style.Color.PINK,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Translated", style=discord.ButtonStyle.green)
    async def translated_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        """
        Show the translated translation and related info
        """
        embed = discord.Embed(
            title=f"Translated: {aiogtrans.LANGUAGES.get(self.translated.dest).capitalize()}",
            description=self.translated.text[:4000],
            timestamp=discord.utils.utcnow(),
            color=style.Color.PINK,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class Translate(commands.Cog):
    """
    Everything to do with translating
    """

    COLOR = style.Color.YELLOW
    ICON = "<:_:992120792827568228>"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init the translate cog
        """
        self.bot = bot
        self.translator = Translator(bot)
        self.translate_menu = app_commands.ContextMenu(
            name="Translate", callback=self.translate_context_menu
        )
        self.bot.tree.add_command(self.translate_menu)

    async def cog_unload(self) -> None:
        """
        On cog unload remove the menu
        """
        self.bot.tree.remove_command(
            self.translate_menu.name, type=self.translate_menu.type
        )

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
        """
        Translate text
        """
        await self.translator.process(ctx.channel, text)

    async def translate_context_menu(
        self, interaction: discord.Interaction, msg: discord.Message
    ) -> None:
        """
        Translate context menu
        """
        await self.translator.process(interaction, msg.content)


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Translate(bot))
