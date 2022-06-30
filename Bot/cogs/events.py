import math

import discord
import discord.utils
from colorama import Fore
from discord.ext import commands, tasks
from gears import style


class Events(commands.Cog):
    """
    Events that I wanna receive but don't really have a cog for
    """

    COLOR = style.Color.BLUE
    ICON = ":clock7:"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init for events
        """
        self.bot = bot
        self.ltd_loop.start()

    async def cog_unload(self) -> None:
        """
        On unload unload timers
        """
        self.ltd_loop.cancel()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """
        When we join a guild print it out
        """
        if guild.get_member(360061101477724170) or (
            await guild.fetch_member(360061101477724170)
        ):
            return

        guild_bots = 0
        for member in guild.members:
            if member.bot:
                guild_bots += 1

        humans = len(guild.members) - guild_bots

        bot_percentage = math.trunc((guild_bots / len(guild.members)) * 10000) / 100

        await self.bot.blogger.bot_info(
            self.bot.blogger.gen_category(f"{Fore.GREEN}JOINED"),
            f" {guild.name} {guild.id} | Server is {bot_percentage}% Bots ({guild_bots}/{len(guild.members)})",
        )

        if bot_percentage > 20 and humans < 5:
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
                color=style.Color.RED,
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
            await self.bot.blogger.bot_info(
                self.bot.blogger.gen_category(f"{Fore.MAGENTA}AUTOLEFT"),
                f" {guild.name} {guild.id}",
            )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """
        When we leave a guild
        """
        await self.bot.blogger.bot_info(
            self.bot.blogger.gen_category(f"{Fore.RED}LEFT"),
            f" {guild.name} {guild.id}",
        )

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread) -> None:
        """
        Whenever possible, join threads
        """
        await thread.join()

    @tasks.loop(seconds=60.0)
    async def ltd_loop(self) -> None:
        """
        the ltd loop that checks if any updates need to be sent
        """
        await self.bot.blogger.ltd()

    @ltd_loop.before_loop
    async def before_ltd_loop(self) -> None:
        """
        Waiting until the bots ready to dispatch the loop
        """
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Events(bot))
