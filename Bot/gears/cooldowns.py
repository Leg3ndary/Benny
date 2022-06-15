"""
This is never actually imported, just a template
"""

import discord
from discord.ext import commands


class CogCooldowns:
    """
    Data class for related commands and cogs
    """
    
    def __init__(self, cog) -> None:
        """
        Init for the cog cooldowns
        """
        
    


class CooldownManager:
    """
    Manage cooldowns through this generic cooldown manager.
    """

    def __init__(self, cc: CogCooldowns) -> None:
        """
        Init
        """
        self.cc = cc
    
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