import io

import PIL as pil
import pytesseract
from discord.ext import commands


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
        Read an image and return the text in it, you should add more choices when you can
        """
        img = await self.loop.run_in_executor(
            None, pil.Image.open, io.BytesIO(image_bytes)
        )
        text = await self.loop.run_in_executor(
            None, pytesseract.pytesseract.image_to_string, img
        )

        return text
