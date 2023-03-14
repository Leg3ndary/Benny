import time

import asqlite
import discord
from discord.ext import commands

from . import style


class AFKManager:
    """
    Manage afk sessions and related data
    """

    pcc = None

    def __init__(self, bot: commands.Bot, database: asqlite.Connection) -> None:
        """
        Init the manager
        """
        self.bot = bot
        self.pcc = bot.pcc  # premium stuff, not done smh
        self.database = database

    async def set_afk(self, ctx: commands.Context, message: str) -> None:
        """
        Set an afk for a user in a certain guild
        """
        query = {"_id": str(ctx.author.id)}
        afk_doc = {
            "_id": str(ctx.author.id),
            "message": message,
            "unix": int(time.time()),
        }
        await self.db[str(ctx.message.guild.id)].replace_one(query, afk_doc, True)

        embed = discord.Embed(
            title="Set AFK",
            description=f""">>> {message}""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        await ctx.send(embed=embed)

    async def del_afk(self, guild: int, user: int) -> None:
        """
        Delete an afk from the db, usually called when a user has sent a message showing that they
        aren't actually afk
        """
        query = {"_id": str(user)}
        await self.db[str(guild)].delete_one(query)

    async def manage_afk(self, message: discord.Message) -> None:
        """
        Manage an afk when it gets sent here, first check if its a message from a user
        """
        query = {"_id": str(message.author.id)}
        afk_data = await self.db[str(message.guild.id)].find_one(query)
        if afk_data:
            if afk_data.get("unix") + 3 < int(time.time()):
                await self.del_afk(message.guild.id, message.author.id)
                embed = discord.Embed(
                    title="Removed AFK",
                    description=f"""Welcome back {message.author.mention}!

                    You've been afk since <t:{afk_data["unix"]}:R>""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.PINK,
                )
                await message.reply(embed=embed)

        for mention in message.mentions[:3]:
            if not message.author.id == mention.id:
                query = {"_id": str(mention.id)}
                afk_data = await self.db[str(message.guild.id)].find_one(query)
                username = (
                    self.bot.get_user(mention.id)
                    or (await self.bot.fetch_user(mention.id))
                ).name
                if afk_data:
                    embed = discord.Embed(
                        title=f"{username} is AFK",
                        description=afk_data["message"],
                        timestamp=discord.utils.utcnow(),
                        color=style.Color.PINK,
                    )
                    await message.channel.send(embed=embed)
