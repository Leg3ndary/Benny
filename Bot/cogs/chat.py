import json

import aiohttp
import discord
from discord.ext import commands
from gears import style

API_URL = "https://api-inference.huggingface.co/models/Leg3ndary/"

class Chat(commands.Cog):
    """
    This cog allows you to chat with our own ai bot
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init the cog
        """
        self.bot = bot
        self.api_endpoint = API_URL + "MichaelScott"
        huggingface_token = bot.config.get("HuggingFace").get("Token")
        self.request_headers = {"Authorization": f"Bearer {huggingface_token}"}
        self.session: aiohttp.ClientSession = bot.sessions.get("chat")

    async def query(self, payload: dict) -> str:
        """
        make request to the Hugging Face model API
        """
        data = json.dumps(payload)
        async with self.session.post(self.api_endpoint, headers=self.request_headers, data=data) as response:
            ret = await response.json()
            return ret

    @commands.hybrid_command(
        name="chat",
        description="""Chat with ai""",
        help="""This ai is trained on Michael Scott's quotes and responds to them""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def chat_cmd(self, ctx: commands.Context, message: str) -> None:
        """
        Chat with the bot
        """
        payload = {"inputs": {"text": message}}

        async with ctx.channel.typing():
            response = await self.query(payload)
        reply = response.get("generated_text", None)

        if not reply:
            if "error" in response:
                reply = f"```yaml\nError: {response['error']}```"
            else:
                reply = "Hmm... something is not right."

        embed = discord.Embed(
            title="AI Chat",
            description=reply,
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREY
        )
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """
    Setup the cog.
    """
    await bot.add_cog(Chat(bot))
