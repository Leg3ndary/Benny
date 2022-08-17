import json
import os

import requests
from discord.ext import commands

API_URL = "https://api-inference.huggingface.co/models/r3dhummingbird/"

class Chat(commands.Cog):
    """
    This cog allows you to chat with our own ai bot
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init the cog
        """
        self.bot = bot
        self.api_endpoint = API_URL + "DialoGPT-medium-joshua"
        # retrieve the secret API token from the system environment
        huggingface_token = os.environ["HUGGINGFACE_TOKEN"]
        # format the header in our request to Hugging Face
        self.request_headers = {"Authorization": f"Bearer {huggingface_token}"}
    
    async def query(self, payload: dict) -> str:
        """
        make request to the Hugging Face model API
        """
        data = json.dumps(payload)
        response = requests.request(
            "POST", self.api_endpoint, headers=self.request_headers, data=data
        )
        ret = json.loads(response.content.decode("utf-8"))
        return ret

    @commands.command(
        name="command",
        description="""Description of command, complete overview with all neccessary info""",
        help="""More help""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def chat(self, ctx: commands.Context, message: str) -> None:
        """
        Chat with the bot
        """
        # form query payload with the content of the message
        payload = {"inputs": {"text": message}}

        # while the bot is waiting on a response from the model
        # set the its status as typing for user-friendliness
        async with ctx.channel.typing():
            response = self.query(payload)
        bot_response = response.get("generated_text", None)

        # we may get ill-formed response if the model hasn't fully loaded
        # or has timed out
        if not bot_response:
            if "error" in response:
                bot_response = f"`Error: {response['error']}`"
            else:
                bot_response = "Hmm... something is not right."

        # send the model's response to the Discord channel
        await ctx.send(bot_response)


async def setup(bot: commands.Bot) -> None:
    """
    Setup the cog.
    """
    await bot.add_cog(Chat(bot))
