"""
This entire cog is dicontinued due to message content privacy issues.
If it ever resurfaces it will be a lot more restricted.
"""

import time

import discord
import discord.utils
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

"""
Snipe Schema

MONGODB (Client)
    SNIPE (Database)
        GUILD_ID (Collection)
            {
                "_id": channel_id str,
                "msg": {
                    "user_id": user id str,
                    "content": message content str,
                    "created_at": message sent time date,
                    "added": the time we added this to our db int
                }
            }
"""


class Snipe(commands.Cog):
    """
    The amazing snipe cog we use for this bot
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init the snipe cog
        """
        self.bot = bot
        self.snipe: AsyncIOMotorClient = None

    async def cog_load(self) -> None:
        """
        Load mongodb for snipe when called
        """
        mongo_uri = (
            self.bot.config.get("Mongo")
            .get("URL")
            .replace("<Username>", self.bot.config.get("Mongo").get("User"))
            .replace("<Password>", self.bot.config.get("Mongo").get("Pass"))
        )
        self.snipe = AsyncIOMotorClient(mongo_uri)["Snipe"]
        await self.bot.blogger.connect("SNIPE MONGODB")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """
        Tracking deleted messages...
        """
        if not message.guild.id or message.author.bot:
            pass

        else:
            coll = self.snipe[str(message.guild.id)]
            patron = False  # Change this later to check the guild
            query_doc = {"_id": str(message.guild.id)}
            channel_snipes = await coll.count_documents(query_doc)

            if not patron:
                max_snipes = 3
            else:
                max_snipes = 10

            if channel_snipes > max_snipes:
                oldest_msg_added = 99999999999
                async for doc in await coll.find(query_doc):
                    if doc.get("added") < oldest_msg_added:
                        oldest_msg_added = doc.get("added")
                        oldest_msg_id = doc.get("_id")
                del_doc = {"_id": oldest_msg_id}
                # Deleting it
                await coll.delete_one(del_doc)

            # Store the message, passed all checks
            snipe_data = {
                "_id": message.id,
                "author": message.author.id,
                "content": message.content,
                "created_at": message.created_at,
                "added": int(time.time()),
            }
            await coll.insert_one(snipe_data)

    @commands.group(
        name="snipe",
        description="""Description of command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def snipe_group(self, ctx: commands.Context, choice=1):
        """Snipe command"""
        if not ctx.invoked_subcommand:
            # coll = await self.snipe[str(ctx.guild.id)]
            return


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    return
    # await bot.add_cog(Snipe(bot))
