import asyncio
import discord
import discord.utils
from discord.ext import commands
from gears import style
from detoxify import Detoxify


class Toxicity:
    """
    Toxicity info for easy access
    """
    
    def __init__(self, prediction: dict) -> None:
        """
        Init

        Parameters
        ----------
        prediction: dict
            The prediction dict to build the Toxicity object off of
        """
        self.toxicity = round(prediction.get("toxicity"), 5)
        self.severe_toxicity = round(prediction.get("severe_toxicity"), 5)
        self.obscene = round(prediction.get("obscene"), 5)
        self.identity_attack = round(prediction.get("identity_attack"), 5)
        self.insult = round(prediction.get("insult"), 5)
        self.threat = round(prediction.get("threat"), 5)
        self.sexual_explicit = round(prediction.get("sexual_explicit"), 5)
        self.average = (self.toxicity + self.severe_toxicity + self.obscene + self.identity_attack + self.insult + self.threat + self.sexual_explicit) / 7


class Sentinel(commands.Cog):
    """
    Sentinel cog, drama watcher, moderation supreme, call it what you want
    """

    def __init__(self, bot):
        self.bot = bot
        self.sentinel = Detoxify(model_type="unbiased")

    async def sentinel_check(self, msg: str) -> Toxicity:
        """
        Check for toxification
        """
        return Toxicity(self.sentinel.predict(msg))

    @commands.Cog.listener()
    async def on_message(self, msg):
        """
        Testing
        """
        if msg.author.bot:
            pass
        elif msg.guild.id == 839605885700669441:
            toxic = await self.sentinel_check(msg.clean_content)
            if toxic.toxicity > 0.6:
                embed = discord.Embed(
                    title=f"Are you being toxic?",
                    description=f"""So rude.
                    toxicity: {toxic.toxicity * 100}%
                    severe_toxicity: {toxic.severe_toxicity * 100}
                    obscene: {toxic.obscene * 100}
                    identity_attack: {toxic.identity_attack * 100}
                    insult: {toxic.insult * 100}
                    threat: {toxic.threat * 100}
                    sexual_explicit: {toxic.sexual_explicit * 100}
                    average: {toxic.average * 100}""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.RED
                )
                await msg.channel.send(embed=embed, delete_after=10)


async def setup(bot):
    await bot.add_cog(Sentinel(bot))
