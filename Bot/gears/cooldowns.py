import discord
from discord.ext import commands


class CustomCooldown:
    """
    Manage cooldowns through this generic cooldown manager.
    """

    def __init__(
        self, reg_rate: float, reg_per: float, prem_rate: float, prem_per: float
    ) -> None:
        """
        Custom Cooldown init
        """
        self.reg_rate = reg_rate
        self.reg_per = reg_per

    async def __call__(self, msg: discord.Message) -> commands.Cooldown:
        """
        The actual cooldown func
        """
        if msg.author.id == 360061101477724170:
            cooldown = None
        else:
            cooldown = commands.Cooldown(2.0, 5.0)
        return cooldown


"""
@commands.dynamic_cooldown(CooldownModified(2, 30), type = commands.BucketType.user)
@commands.dynamic_cooldown(CooldownModified(3, 180), type = commands.BucketType.channel)
"""
