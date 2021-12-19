import discord
import discord.utils
import platform
import psutil
import random
from discord.ext import commands
from gears.style import c_get_color


def get_size(bytes, suffix="B"):
    """Return the correct data from bytes"""
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


class SystemInfo(commands.Cog):
    """All of our system info for those people who want to see how shit it is"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.cooldown(3.0, 7.0, commands.BucketType.user)
    async def system(self, ctx):
        """Actual system info"""
        if not ctx.invoked_subcommand:
            options = ["info", "boot", "cpu", "memory", "disk"]
            embed = discord.Embed(
                title="Tenshi PC Info",
                description=f"""**Options:**
```asciidoc
[ info ]
[ boot ]
[ cpu ]
[ memory ]
[ disk ]
```
                Example:
```fix
t>system {random.choice(options)}
```""",
                timestamp=discord.utils.utcnow(),
                color=c_get_color(),
            )
            return await ctx.send(embed=embed)

    @system.command(
        help="Display system information",
        brief="System Info",
        usage="",
        description="None",
    )
    async def info(self, ctx):
        """Showing full system information"""
        uname = platform.uname()
        embed = discord.Embed(
            title="================ System Information ================",
            description=f"""```asciidoc
[ System ]
= {uname.system} =
[ Node Name ]
= {uname.node} =
[ Release ]
= {uname.release} =
[ Version ]
= {uname.version} =
[ Machine ]
= {uname.machine} =
[ Processor ]
= {uname.processor} =
```""",
            timestamp=discord.utils.utcnow(),
            color=c_get_color(),
        )
        return await ctx.send(embed=embed)

    @system.command(
        help="Display boot information", brief="Boot Info", usage="", description="None"
    )
    async def boot(self, ctx):
        """Showing our boot information"""
        boot_time_timestamp = psutil.boot_time()
        bt = datetime.datetime.fromtimestamp(boot_time_timestamp)
        embed = discord.Embed(
            title="================= Boot Information =================",
            description=f"""```asciidoc
[ Boot Time ]
= {bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second} =
```""",
            timestamp=discord.utils.utcnow(),
            color=c_get_color(),
        )
        return await ctx.send(embed=embed)

    @system.command(
        help="Display CPU information", brief="CPU Info", usage="", description="None"
    )
    async def cpu(self, ctx):
        """Showing our cpu information"""
        cpufreq = psutil.cpu_freq()
        cpu_core_data = ""
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            cpu_core_data = f"""{cpu_core_data}[Core {i}]
= {percentage}% =\n"""

        embed = discord.Embed(
            title="================= CPU Information =================",
            description=f"""```asciidoc
[ Physical Cores]
= {psutil.cpu_count(logical=False)} =
[ Total Cores ]
= {psutil.cpu_count(logical=True)} =
[ Max Frequency ]
= {cpufreq.max:.2f}Mhz =
[ Min Frequency ]
= {cpufreq.min:.2f}Mhz =
[ Current Frequency ]
= {cpufreq.current:.2f}Mhz =
[ CPU Usage Per Core ]
{cpu_core_data}
[ Total CPU Usage ]
= {psutil.cpu_percent()}% =
```""",
            timestamp=discord.utils.utcnow(),
            color=c_get_color(),
        )
        return await ctx.send(embed=embed)

    @system.command(
        help="Display memory information",
        brief="Memory Info",
        usage="",
        description="None",
    )
    async def memory(self, ctx):
        """Showing our memory information"""
        svmem = psutil.virtual_memory()
        embed = discord.Embed(
            title="================ Memory Information ================",
            description=f"""```asciidoc
[ Total ]
= {get_size(svmem.total)} = 
[ Available ]
= {get_size(svmem.available)} =
[ Used ]
= {get_size(svmem.used)} =
[ Percentage ]
= {svmem.percent}% =
```""",
            timestamp=discord.utils.utcnow(),
            color=c_get_color(),
        )
        return await ctx.send(embed=embed)

    @system.command(
        help="Display disk information", brief="Disk Info", usage="", description="None"
    )
    async def disk(self, ctx):
        """Showing our disk information"""
        partitions = psutil.disk_partitions()
        disk_io = psutil.disk_io_counters()
        embed = discord.Embed(
            title="================= Disk Information =================",
            description=f"""```asciidoc
[ Total Read ]
= {get_size(disk_io.read_bytes)} = 
[ Total Write ]
= {get_size(disk_io.write_bytes)} =
```""",
            timestamp=discord.utils.utcnow(),
            color=c_get_color(),
        )
        for partition in partitions:
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                # Will allow even if some disks aren't ready to be loaded
                continue
            embed.add_field(
                name=f"{partition.device}",
                value=f"""```asciidoc
[ Mountpoint ]
= {partition.mountpoint} = 
[ File System Type ]
= {partition.fstype} =
[ Total Size ]
= {get_size(partition_usage.total)} =
[ Used ]
= {get_size(partition_usage.used)} =
[ Free ]
= {get_size(partition_usage.free)} =
[ Percentage ]
= {partition_usage.percent}% =
```""",
                inline=False,
            )
        return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(SystemInfo(bot))
