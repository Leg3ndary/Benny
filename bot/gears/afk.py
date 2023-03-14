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
        async with self.database.cursor() as cursor:
            await cursor.execute(
                "REPLACE INTO base_afk VALUES (?, ?, ?, ?);",
                (
                    str(ctx.message.guild.id),
                    str(ctx.author.id),
                    message,
                    int(time.time()),
                ),
            )
            await self.database.commit()

        embed = discord.Embed(
            title="Set AFK",
            description=f""">>> {message}""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        embed.set_footer(
            text="To remove this AFK send a message anywhere",
            icon_url=ctx.author.avatar.url,
        )
        await ctx.reply(embed=embed)

    async def del_afk(self, guild: int, user: int) -> None:
        """
        Delete an afk from the db, usually called when a user has sent a message showing that they
        aren't actually afk
        """
        async with self.database.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM base_afk WHERE guild = ? AND user = ?;",
                (str(guild), str(user)),
            )
            await self.database.commit()

    async def manage_afk(self, message: discord.Message) -> None:
        """
        Manage an afk when it gets sent here, first check if its a message from a user
        """
        async with self.database.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM base_afk WHERE guild = ? AND user = ?;",
                (str(message.guild.id), str(message.author.id)),
            )
            afk_data = await cursor.fetchone()
            if afk_data:
                if afk_data[3] + 3 < int(time.time()):
                    await self.del_afk(message.guild.id, message.author.id)
                    embed = discord.Embed(
                        title="Removed AFK",
                        description=f"""Welcome back {message.author.mention}!

                        You've been afk since <t:{afk_data[3]}:R>""",
                        timestamp=discord.utils.utcnow(),
                        color=style.Color.PINK,
                    )
                    await message.reply(embed=embed)

            for mention in message.mentions[:3]:
                if not message.author.id == mention.id:
                    await cursor.execute(
                        "SELECT * FROM base_afk WHERE guild = ? AND user = ?;",
                        (str(message.guild.id), str(mention.id)),
                    )
                    afk_data = await cursor.fetchone()
                    username = (
                        self.bot.get_user(mention.id)
                        or (await self.bot.fetch_user(mention.id))
                    ).name
                    if afk_data:
                        embed = discord.Embed(
                            title=f"{username} is AFK",
                            description=afk_data[2],
                            timestamp=discord.utils.utcnow(),
                            color=style.Color.PINK,
                        )
                        await message.channel.send(embed=embed)
