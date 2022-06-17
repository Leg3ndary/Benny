import discord
from discord.ext import commands
from motor import motor_asyncio


class CustomCooldown:
    """
    Manage cooldowns through this generic cooldown manager.
    """

    def __init__(
        self,
        reg_rate: float = 2.0,
        reg_per: float = 5.0,
        prem_rate: float = 2.0,
        prem_per: float = 3.5
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
