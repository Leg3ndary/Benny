import asqlite
import discord
import discord.utils
from discord.ext import commands
from gears import style

"""
Non Premium
- Enable or disable logs
- Set custom channels for each

Premium
- Change avatar and username for logs
"""


class LoggingManager:
    """
    Webhook manager, mainly used to make methods a lot more clear
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Init
        """
        self.bot = bot
        self.db: asqlite.Connection = None

    async def load_db(self) -> None:
        """
        Load our db on start
        """
        self.db = await asqlite.connect("databases/logging.db")
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS webhooks (
                id          TEXT NOT NULL
                                PRIMARY KEY,
                type        TEXT NOT NULL,
                webhook_url TEXT NOT NULL,
                username    TEXT,
                avatar      TEXT
            );
            """
        )
        await self.db.commit()
        await self.bot.blogger.load("Logging")

    async def create_webhook(
        self, channel: discord.TextChannel, username: str = None, avatar: str = None
    ) -> None:
        """Create a webhook"""


class Logging(commands.Cog):
    """
    Custom server logging
    """

    COLOR = style.Color.PURPLE
    ICON = "📰"

    def __init__(self, bot: commands.Bot) -> None:
        """
        Logging init
        """
        self.bot = bot
        self.logging_manager: LoggingManager = None

    async def cog_load(self) -> None:
        """
        On Cog Load
        """
        self.logging_manager = LoggingManager(self.bot)
        await self.logging_manager.load_db()

    @commands.hybrid_group(
        name="logs",
        description="""List log settings""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=["logging"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def logs_cmd(self, ctx: commands.Context) -> None:
        """
        View basic log config
        """
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Logging(bot))
