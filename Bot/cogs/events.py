import math

import discord
import discord.utils
from colorama import Fore
from discord.ext import commands
from gears import style


class Events(commands.Cog):
    """
    Events that I wanna receive but don't really have a cog for
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """
        When we join a guild print it out
        """
        if guild.get_member(360061101477724170):
           return     

        guild_bots = 0
        for member in guild.members:
            if member.bot:
                guild_bots += 1

        humans = len(guild.members) - guild_bots

        bot_percentage = math.trunc((guild_bots / len(guild.members)) * 10000) / 100

        await self.bot.printer.p_bot(
            await self.bot.printer.generate_category(f"{Fore.GREEN}JOINED"),
            f" {guild.name} {guild.id} | Server is {bot_percentage}% Bots ({guild_bots}/{len(guild.members)})",
        )

        if bot_percentage > 20 and humans < 19:
            sent = False
            embed = discord.Embed(
                title=f"Sorry!",
                description=f"""Your server has **{guild_bots} Bots ** compared to **{len(guild.members)} Members**
                Either:
                - Have `20+` humans
                Currently **{humans}** humans
                - Lower your servers percentage of bots to under 20%
                Currently **{bot_percentage}%** bots""",
                timestamp=discord.utils.utcnow(),
                color=style.get_color("red"),
            )
            for channel in guild.channels:
                if "general" in channel.name:
                    await channel.send(embed=embed)
                    sent = True
                    break
            if not sent:
                try:
                    await guild.channels[0].send(embed=embed)
                except:
                    pass
            await guild.leave()
            await self.bot.printer.p_bot(
                await self.bot.printer.generate_category(f"{Fore.MAGENTA}AUTOLEFT"),
                f" {guild.name} {guild.id}",
            )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """
        When we leave a guild
        """
        await self.bot.printer.p_bot(
            await self.bot.printer.generate_category(f"{Fore.RED}LEFT"),
            f" {guild.name} {guild.id}",
        )


async def setup(bot):
    await bot.add_cog(Events(bot))
