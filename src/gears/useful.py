import os
import asyncio
import json
import aiofiles

def load_cogs(bot, cogs):
    """Generate a cog list based on the given cog directory"""
    cog_list = []
    for file in cogs:
        try:
            if file.endswith(".py"):
                bot.load_extension(f"cogs.{file[:-3]}")
                cog_list.append(f"cogs.{file[:-3]}")
                print(f"Loaded {file[:-3]}")

        except Exception as e:
            print(f"Cog {file[:-3]} failed loading\nError: {e}")

    bot.cog_list = cog_list


async def update_config(self, ctx):
    """"""