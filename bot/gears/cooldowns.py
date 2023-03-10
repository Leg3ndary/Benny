import discord
from discord.ext import commands


class PremiumChecker:
    """
    Class to interact with our db and check if a command is premium
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        PremiumChecker mainly to be used with cooldowns
        """
        self.bot = bot
        self.loop = bot.loop

    async def _guild_premium(self, _id: int) -> bool:
        """
        Internal async method to be called because
        """

    def guild_premium(self, _id: int) -> bool:
        """
        Check if a guild is premium
        """
        return self.loop.run_in_executor(None, self._guild_premium, _id)


class CustomCooldown:
    """
    Manage cooldowns through this generic cooldown manager.
    """

    def __init__(
        self,
        reg_rate: float = 2.0,
        reg_per: float = 5.0,
        prem_rate: float = 2.0,
        prem_per: float = 3.5,
    ) -> None:
        """
        Custom Cooldowns

        Parameters
        ----------
        reg_rate: float
            The regular rate, default 2.0
        reg_per: float
            The regular per, default 5.0
        prem_rate: float
            The premium rate, default 2.0
        prem_per: float
            The premium per, default 3.5
        """
        self.reg_rate = reg_rate
        self.reg_per = reg_per
        self.prem_rate = prem_rate
        self.prem_per = prem_per

    def __call__(self, msg: discord.Message) -> commands.Cooldown:
        """
        The actual cooldown func
        """
        if msg.author.id == 360061101477724170:
            cooldown = None
        else:
            cooldown = commands.Cooldown(self.reg_rate, self.reg_per)
        return cooldown


"""
@commands.dynamic_cooldown(CooldownModified(2, 30), type = commands.BucketType.user)
@commands.dynamic_cooldown(CooldownModified(3, 180), type = commands.BucketType.channel)
"""

# def get_cooldown(ctx: commands.Context) -> commands.Cooldown:
#     """
#     Gets the cooldown for a command
#     """
#     bot = ctx.bot

#     is_premium = None # Prob use some bot attr

# def get_app_cooldown(interaction: discord.Interaction) -> app_commands.Cooldown:
#     """
#     Gets the cooldown for an app command
#     """
#     bot = interaction.bot

#     is_premium = None # Prob use some bot attr

# Import the func everywhere

# @commands.dynamic_cooldown(get_cooldown, type=commands.BucketType.user) # or whatever
# @commands.command()
# async def cmd(ctx: commands.Context) -> None:
#     """
#     Some command
#     """
#     await ctx.send("test")

# @tree.command()
# @app_commands.checks.dynamic_cooldown(get_cooldown)
# async def cmd(interaction):
#     await interaction.response.send_message("test")
