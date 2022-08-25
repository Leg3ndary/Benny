import asyncio
import datetime
import json

import asqlite
import discord
import parsedatetime
from discord.ext import commands
from gears import style

with open("Assets/timezoneinfo.json", encoding="utf-8") as f:
    TIMEZONE_INFO = json.load(f)

CHOICES = []

for TIMEZONE in TIMEZONE_INFO:
    CHOICES.append(
        discord.app_commands.Choice(
            name=f'{TIMEZONE.get("value")} {TIMEZONE.get("text").split(" ", 1)[0]}',
            value=float(TIMEZONE.get("offset")),
        )
    )
    print(CHOICES)


class ReminderTimeDropdown(discord.ui.Select):
    """
    ReminderTimeDropdown
    """

    def __init__(self) -> None:
        super().__init__()


class ReminderView(discord.ui.View):
    """
    Reminder View to help select and keep everything smooth
    """

    def __init__(self, time: int) -> None:
        """
        Construct the Reminder View
        """
        super().__init__()

    @discord.ui.button(
        style=discord.ButtonStyle.primary,
        label="Confirm",
        emoji=style.Emoji.REGULAR.check,
    )
    async def confirm_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Confirm the reminder should be saved and dispatched when neccessary
        """


class ReminderManager:
    """
    Reminder Task Manager
    """

    def __init__(self, bot: commands.Bot, db: asqlite.Connection) -> None:
        """
        Constructs all the necessary attributes for our Reminder Manager
        """
        self.REMINDER_LIMIT: int = 25
        self.bot = bot
        self.db = db
        self.remind_id: int = None
        self.active_reminders: dict[str, asyncio.Task] = {}

    async def create_table(self) -> None:
        """
        Create a table for our stuff :D
        """
        await self.db.execute(
            """
            CREATE TABLE users (
                id           TEXT    PRIMARY KEY
                                    NOT NULL,
                patron_level INTEGER NOT NULL
                                    DEFAULT (0),
                blacklisted  BOOLEAN DEFAULT (False)
                                    NOT NULL,
                timezone     TEXT    DEFAULT NULL
            );
            """
        )

    async def load_config(self) -> None:
        """
        Start setting up the config for the reminders
        """
        self.remind_id = await self.bot.redis.get("Reminder_Count")
        if not self.remind_id:
            await self.bot.redis.set("Reminder_Count", "1")
            self.remind_id = 1
        else:
            self.remind_id = int(self.remind_id)

    async def increment_reminder_id(self) -> None:
        """
        Increment the reminder id
        """
        self.remind_id += 1
        await self.bot.redis.set("Reminder_Count", self.remind_id)

    async def load_reminders(self) -> None:
        """
        Load all our reminders and timers and queue them when the bot is started so reminders actually get sent
        """
        await self.load_config()
        await self.create_table()

        async with self.db.execute("""SELECT * FROM reminders;""") as cursor:
            results = await cursor.fetchall()

        for reminder in results:
            await self.create_timer(reminder[0], reminder[1], 0, "reminder")  # not done

    async def queue_reminder(
        self, rid: int, uid: str, time: int, reminder: str
    ) -> None:
        """
        Queue a reminder to be sent
        """
        await asyncio.sleep(time)
        user = self.bot.get_user(uid) or (await self.bot.fetch_user(uid))

        embed = discord.Embed(
            title="",
            description="""""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        await user.send(embed=embed)

    async def create_reminder(
        self, rid: int, uid: str, time: int, reminder: str
    ) -> None:
        """
        Create a timer and dispatch.
        """
        await self.db.execute(
            """
            INSERT INTO reminders VALUES(?, ?, ?, ?, ?);
            """,
            (rid, uid, time, reminder, False),
        )
        await self.db.commit()
        self.active_reminders.update(
            rid, asyncio.create_task(self.queue_reminder(rid, uid, time, reminder))
        )


class Reminders(commands.Cog):
    """
    Reminder cog for reminders, literally what else
    """

    COLOR = style.Color.LIME
    ICON = ":reminder_ribbon:"

    def __init__(self, bot: commands.Bot):
        """
        Construct the reminder cog
        """
        self.bot = bot
        self.reminders_db: asqlite.Connection = None
        self.rm: ReminderManager = None
        self.calendar = parsedatetime.Calendar()

    async def cog_load(self):
        """
        Dispatch to start load reminders
        """
        self.reminders_db = await asqlite.connect("Databases/users.db")
        self.rm = ReminderManager(self.bot, self.reminders_db)

    async def pull_time(self, string: str) -> int:
        """
        Pull the time from a string
        """
        (
            time_struct,
            parse_status,  # pylint: disable=unused-variable
        ) = self.calendar.parse(string)
        """if parse_status == 0:
            raise commands.BadArgument("Time not found")"""
        return int(datetime.datetime(*time_struct[:6]).timestamp())

    @commands.Cog.listener()
    async def on_load_reminders(self) -> None:
        """
        Load reminders
        """
        await self.rm.load_reminders()

    @commands.command(
        name="remind",
        description="""Uses a task manager to create, send, limit, reminders.""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=["rm"],
        enabled=False,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def reminder_cmd(self, ctx: commands.Context, *, reminder: str) -> None:
        """
        Remind yourself of something
        """
        unix = await self.pull_time(reminder)

        if unix < datetime.datetime.now().timestamp():
            unix = 0

        embed = discord.Embed(
            title="Creating Reminder",
            description=f""">>> {reminder}

            {datetime.datetime.now().timestamp()}
            {unix}""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREY,
        )
        await ctx.send(embed=embed)  # , view=ReminderView(time))

    @commands.command(
        name="timezone",
        description="""A command to set your timezone""",
        help="""A command to set your timezone""",
        brief="A command to set your timezone",
        aliases=[],
        enabled=False,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def timezone_cmd(self, ctx: commands.Context, timezone: str = None) -> None:
        """
        A command to set your timezone
        """
        embed = discord.Embed(
            title="",
            description="""""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.random(),
        )
        await ctx.send(embed=embed)

    # @discord.app_commands.command(
    #     name="timezone",
    #     description="""A command to set your timezone""",
    # )
    # @discord.app_commands.choices(
    #     timezone=CHOICES
    # )
    # async def timezone_slash_cmd(self, interaction: commands.Context, timezone: discord.app_commands.Choice[float]) -> None:
    #     """
    #     A command to set your timezone
    #     """
    #     embed = discord.Embed(
    #         title="You chose",
    #         description=f"""{timezone}""",
    #         timestamp=discord.utils.utcnow(),
    #         color=style.Color.random()
    #     )
    #     await interaction.response.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Reminders(bot))
