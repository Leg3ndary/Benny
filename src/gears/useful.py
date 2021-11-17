from gears.style import c_get_color, c_get_emoji
import discord.utils
import discord


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
    """Generate a cog list based on the given cog directory"""
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


async def update_config(self, ctx):
    """"""


async def report_error(bot, error_descrip):
    """Report an error by directly direct messaging me."""
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
