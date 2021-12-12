from gears.style import c_get_color, c_get_emoji
import discord.utils
import discord
from discord.ext import commands


def len_file(file: str) -> int:
    """Return the file length for a given file"""
    try:
        with open(file, encoding="utf8") as f:
            for i, l in enumerate(f):
                pass
        return i + 1
    except Exception as e:
        print(e)
        return 0


def load_cogs(bot, cogs):
    """
    Print and load a live feed, 
        Parameters:
            bot (obj): Bot Instance
            cogs (list): List of files that are in cogs in src/cogs
    """
    cog_list = []
    for file in cogs:
        try:
            if (
                file.endswith(".py")
                and not file.endswith("cog_template.py")
                and not file.endswith("redis.py")
                and not file.endswith("pastebin.py")
            ):
                bot.load_extension(f"cogs.{file[:-3]}")
                cog_list.append(f"cogs.{file[:-3]}")
                print(f"Loaded {file[:-3]}")

        except Exception as e:
            print(f"Cog {file[:-3]} failed loading\nError: {e}")

    bot.cog_list = cog_list


async def update_config(ctx):
    """"""


async def report_error(bot, error_descrip):
    """
    Report an error by directly direct messaging me.
        Parameters:
            bot (obj): Bot Instance
            error_descrip (str): Error description/message
    """

    ben = bot.get_user(360061101477724170)
    if not ben:
        ben = await bot.fetch_user(360061101477724170)

    embed = discord.Embed(
        title=f"Error Report",
        description=f"""""",
        timestamp=discord.utils.utcnow(),
        color=await c_get_color("red"),
    )
    embed.set_thumbnail(url=c_get_emoji("image", "cancel"))
    await ben.send(embed=embed)


def default_cooldown_manager(msg, global_db):
    """
    Manage cooldowns
        Version:
            Default
        Parameters:
            msg (obj): The message object, basically context
            global_db (obj): Our global db that contains all the info that we need to check against
    """
    user = global_db.find_one({"_id": msg.author.id})

    # Checking if the user is a patron and his/her level

    if user.get("PatronLevel") == 3:
        return commands.Cooldown(3.0, 5.0)
    elif user.get("PatronLevel") == 2:
        return commands.Cooldown(3.0, 6.0)
        

    #if msg.author.permissions.manage_messages:
        #return None
    #elif discord.utils.get(msg.author.roles, name="Nitro Booster"):
        #return commands.Cooldown(2, 60)  # 2 per minute
    # 3 Commands per 8 seconds if nothings been set
    return commands.Cooldown(3.0, 8.0)