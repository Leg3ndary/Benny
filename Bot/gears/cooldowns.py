from discord.ext import utils, commands

class CooldownManager:
    """
    Manage what we return from cooldowns"""

def custom_cooldown(message):
    if message.author.permissions.manage_messages:
        return None  # no cooldown
    elif utils.get(message.author.roles, name="Nitro Booster"):
        return commands.Cooldown(2, 60)  # 2 per minute
    return commands.Cooldown(1, 60)  # 1 per minute

@commands.dynamic_cooldown(custom_cooldown, commands.BucketType.user)
