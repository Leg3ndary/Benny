import asyncio
import cleantext
import discord
import discord.utils
from discord.ext import commands
from gears import style


class Welcome(commands.Cog):
    """
    Anything to deal with welcoming or leaving"""

    def __init__(self, bot):
        self.bot = bot

    async def clean_username(self, username: str) -> str:
        """
        Clean a username
        
        Parameters
        ----------
        username: str
            The username to clean
            
        Returns
        -------
        str
            The cleaned username
        """
        new_username = cleantext.clean(username,
            fix_unicode=True,
            to_ascii=True,
            lower=False,
            no_line_breaks=True,
            no_urls=True,
            no_emails=True,
            no_phone_numbers=True,
            no_numbers=False,
            no_digits=False,
            no_currency_symbols=False,
            no_punct=False,
            replace_with_url="<URL>",
            replace_with_email="<EMAIL>",
            replace_with_phone_number="<PHONE>",
            lang="en"
        )
        return new_username

async def setup(bot):
    await bot.add_cog(Welcome(bot))