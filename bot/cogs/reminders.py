import asyncio
import datetime
from typing import Dict, Optional, Tuple

import asqlite
import discord
import parsedatetime
from discord.ext import commands
from gears import style
from interfaces.database import BennyDatabases


class ActiveReminder:
    """
    Represents an reminder state on the bot
    """

    def __init__(self, rid: int, uid: int, time: int, reminder: str) -> None:
        """
        Construct the reminder
        """
        self.rid = rid
        self.uid = uid
        self.time = time
        self.reminder = reminder
        self._task: Optional[asyncio.Task] = None

    async def delete(self, db: asqlite.Connection) -> None:
        """
        Delete the reminder
        """
        await db.execute("DELETE FROM reminders WHERE rid = ?;", (self.rid,))
        await db.commit()
        if not self._task.cancelled:
            self._task.cancel()


class ReminderManager:
    """
    Reminder Task Manager
    """

    def __init__(self, bot: commands.Bot, db: asqlite.Connection) -> None:
        """
        Constructs all the necessary attributes for our Reminder Manager
        """
        self.REMINDER_LIMIT: int = 10
        self.bot = bot
        self.databases: BennyDatabases = bot.databases
        self.remind_id: int = None
        self.active_reminders: Dict[int, ActiveReminder] = {}

    async def create_table(self) -> None:
        """
        Create a table for our stuff :D
        """
        await self.databases.users.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders_users (
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
        await self.databases.users.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders_reminders (
                rid          INTEGER PRIMARY KEY
                                    NOT NULL,
                uid          INTEGER  NOT NULL,
                time         INTEGER NOT NULL,
                reminder     TEXT    NOT NULL
            );
            """
        )
        await self.databases.users.commit()

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

    async def increment_reminder_id(self) -> int:
        """
        Increment the reminder id
        """
        self.remind_id += 1
        await self.bot.redis.set("Reminder_Count", self.remind_id)
        return self.remind_id

    async def load_reminders(self) -> None:
        """
        Load all our reminders and timers and queue them when the bot is started so reminders actually get sent
        """
        await self.load_config()
        await self.create_table()

        async with self.databases.users.execute("""SELECT * FROM reminders_reminders;""") as cursor:
            results = await cursor.fetchall()

        for result in results:
            reminder = ActiveReminder(result[0], result[1], result[2], result[3])
            task = asyncio.create_task(self.queue_reminder(reminder))
            reminder._task = task
            self.active_reminders[result[0]] = reminder

    async def queue_reminder(self, reminder: ActiveReminder) -> None:
        """
        Queue a reminder to be sent
        """
        user = self.bot.get_user(reminder.uid) or (
            await self.bot.fetch_user(reminder.uid)
        )
        if int(reminder.time) - round(datetime.datetime.now().timestamp()) <= 0:
            embed = discord.Embed(
                title="Reminder - This reminder is late, apologies.",
                description=f""">>> {reminder.reminder}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.AQUA,
            )
            embed.set_footer(text=f"Reminder ID: {reminder.rid}")
            await user.send(embed=embed)
            await reminder.delete(self.db)
        else:
            await asyncio.sleep(
                int(reminder.time) - round(datetime.datetime.now().timestamp())
            )
            await reminder.delete(self.db)
            embed = discord.Embed(
                title="Reminder",
                description=f""">>> {reminder.reminder}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.AQUA,
            )
            embed.set_footer(text=f"Reminder ID: {reminder.rid}")
            await user.send(embed=embed)

    async def create_reminder(self, uid: int, time: int, reminder: str) -> int:
        """
        Create a timer and dispatch.

        Returns the created reminder id
        """
        if len(await self.fetch_reminders(uid)) >= self.REMINDER_LIMIT:
            raise commands.BadArgument("You have reached the reminder limit.")

        rid = await self.increment_reminder_id()
        await self.databases.users.execute(
            """
            INSERT INTO reminders_reminders VALUES(?, ?, ?, ?);
            """,
            (rid, uid, time, reminder),
        )
        await self.db.commit()
        reminder = ActiveReminder(rid, uid, time, reminder)
        task = asyncio.create_task(self.queue_reminder(reminder))
        reminder._task = task
        self.active_reminders[rid] = reminder
        return rid

    async def fetch_reminders(self, uid: int) -> Tuple[ActiveReminder]:
        """
        Fetch all reminders for a user
        """
        async with self.databases.users.execute(
            """SELECT * FROM reminders_reminders WHERE uid = ?;""", (uid,)
        ) as cursor:
            results = await cursor.fetchall()
        return tuple(ActiveReminder(*result) for result in results)

    async def fetch_reminder(self, rid: int) -> Optional[ActiveReminder]:
        """
        Fetch a reminder from a remind id
        """
        async with self.databases.users.execute(
            """SELECT * FROM reminders_reminders WHERE rid = ?;""", (rid,)
        ) as cursor:
            result = await cursor.fetchone()
            if result:
                return ActiveReminder(*result)
            return None

    async def delete_reminder(self, rid: int) -> None:
        """
        Delete and cancel a reminder
        """
        await self.active_reminders[rid].delete(self.db)
        self.active_reminders.pop(rid)


class ReminderTimeDropdown(discord.ui.Select):
    """
    ReminderTimeDropdown
    """

    def __init__(self, parsed: Optional[int]) -> None:
        """
        Init the ReminderTimeDropdown

        First value will be the parsed time, if it exists.
        """
        super().__init__()
        times = (
            60,
            300,
            600,
            900,
            1800,
            3600,
            7200,
            10800,
            21600,
            43200,
            86400,
            172800,
            259200,
            604800,
            1209600,
            1814400,
            2419200,
        )
        times_named = (
            "1 minute",
            "5 minutes",
            "10 minutes",
            "15 minutes",
            "30 minutes",
            "1 hour",
            "2 hours",
            "3 hours",
            "6 hours",
            "12 hours",
            "1 day",
            "2 days",
            "3 days",
            "1 week",
            "2 weeks",
            "3 weeks",
            "4 weeks",
        )
        if parsed:
            self.add_option(
                label=datetime.datetime.fromtimestamp(parsed).strftime(
                    "On %A %d %b %Y at %I:%M %p"
                ),
                value=parsed,
            )
        for i in enumerate(times):
            if parsed != i[1] + round(datetime.datetime.now().timestamp()):
                self.add_option(
                    label=f"In {times_named[i[0]]}",
                    value=i[1] + round(datetime.datetime.now().timestamp()),
                )

    async def callback(self, interaction: discord.Interaction) -> None:
        """
        Callback for ReminderTimeDropdown
        """
        self.view.chosen_time = self.values[0]
        await interaction.response.defer()


class ReminderView(discord.ui.View):
    """
    Reminder View to help select and keep everything smooth
    """

    def __init__(
        self, rm: ReminderManager, parsed: Optional[int], reminder: str
    ) -> None:
        """
        Construct the Reminder View
        """
        super().__init__()
        self.rm = rm
        self.chosen_time: int = None
        self.add_item(ReminderTimeDropdown(parsed))
        self.reminder = reminder

    @discord.ui.button(
        style=discord.ButtonStyle.green,
        label="Confirm",
        emoji=style.Emoji.REGULAR.check,
        row=2,
    )
    async def confirm_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Confirm the reminder should be saved and dispatched when neccessary
        """
        if self.chosen_time:
            rid = await self.rm.create_reminder(
                interaction.user.id, self.chosen_time, self.reminder
            )
            embed = discord.Embed(
                title="Created Reminder Successfully",
                description=f""">>> {self.reminder}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREEN,
            )
            embed.set_footer(
                text=f"Reminder ID: {rid}, will send at {datetime.datetime.fromtimestamp(int(self.chosen_time)).strftime('%A %d %b %Y at %I:%M %p')}"
            )
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            embed = discord.Embed(
                title="Error",
                description="""You need to select a time for the reminder.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.RED,
            )
            await interaction.response.send_message(embed=embed)

    # @discord.ui.button(
    #     style=discord.ButtonStyle.blurple,
    #     label="Change Reminder",
    #     emoji=style.Emoji.REGULAR.shuffle
    # )
    # async def change_reminder_button(self, interaction: discord.Interaction, button: discord.Button) -> None:
    #     """
    #     Change the reminder
    #     """

    @discord.ui.button(
        style=discord.ButtonStyle.red,
        label="Cancel",
        emoji=style.Emoji.REGULAR.cancel,
        row=2,
    )
    async def cancel_button(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        """
        Cancel the reminder
        """
        embed = discord.Embed(
            title="Cancelled Reminder Creation Successfully",
            description=f""">>> {self.reminder}""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.RED,
        )
        await interaction.response.edit_message(embed=embed, view=None)


class Reminders(commands.Cog):
    """
    Reminder cog for reminders, literally what else
    """

    COLOR = style.Color.LIME
    ICON = "🎗️"

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
        self.reminders_db = await asqlite.connect("databases/users.db")
        self.rm = ReminderManager(self.bot, self.reminders_db)

    async def pull_time(self, string: str) -> int:
        """
        Pull the time from a string
        """
        (
            time_struct,
            parse_status,  # pylint: disable=unused-variable
        ) = self.calendar.parse(string)
        """
        if parse_status == 0:
            raise commands.BadArgument("Time not found")
        """
        return int(datetime.datetime(*time_struct[:6]).timestamp())

    @commands.Cog.listener()
    async def on_load_reminders(self) -> None:
        """
        Load reminders
        """
        await self.rm.load_reminders()

    @commands.hybrid_group(
        name="reminder",
        description="""Description of command""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(2.0, 5.0, commands.BucketType.user)
    async def reminder_group(self, ctx: commands.Context) -> None:
        """
        Reminder group
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @commands.command(
        name="remind",
        description="""Shorter way to create a reminder.""",
        help="""Shorter way to create a reminder.""",
        brief="Shorter way to create a reminder.",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def remind_cmd(self, ctx: commands.Context, *, reminder: str) -> None:
        """
        Shorter way to create a reminder
        """
        unix = await self.pull_time(reminder)

        if unix < datetime.datetime.now().timestamp():
            unix = None

        embed = discord.Embed(
            title="Creating Reminder",
            description=f""">>> {reminder}""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREY,
        )
        embed.set_footer(text="This is what your reminder will look like")
        await ctx.reply(embed=embed, view=ReminderView(self.rm, unix, reminder))

    @reminder_group.command(
        name="create",
        description="""Remind yourself of something in the future.""",
        help="""Remind yourself of something in the future.""",
        brief="Remind yourself of something in the future.",
        aliases=["remind", "add"],
        enabled=True,
        hidden=False,
    )
    async def reminder_create_cmd(
        self, ctx: commands.Context, *, reminder: str
    ) -> None:
        """
        Remind yourself of something
        """
        unix = await self.pull_time(reminder)

        if unix < datetime.datetime.now().timestamp():
            unix = None

        embed = discord.Embed(
            title="Creating Reminder",
            description=f""">>> {reminder}""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREY,
        )
        embed.set_footer(text="This is what your reminder will look like")
        await ctx.reply(embed=embed, view=ReminderView(self.rm, unix, reminder))

    @reminder_group.command(
        name="list",
        description="""List your current reminders.""",
        help="""List your current reminders.""",
        brief="List your current reminders.",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    async def reminder_list_cmd(self, ctx: commands.Context) -> None:
        """
        List your current reminders.
        """
        reminders = await self.rm.fetch_reminders(ctx.author.id)
        embed = discord.Embed(
            title="Your Reminders",
            description=f">>> You currently have {len(reminders)} reminder{'s' if len(reminders) > 1 else ''}.",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA,
        )
        for reminder in reminders:
            embed.add_field(
                name=f"Reminder ID: {reminder.rid}",
                value=f"""**Date:** {discord.utils.format_dt(datetime.datetime.fromtimestamp(int(reminder.time)), style='F')}
                **Reminder:** {reminder.reminder[:100]}""",
                inline=False,
            )
        await ctx.reply(embed=embed)

    @reminder_group.command(
        name="delete",
        description="""Delete a reminder.""",
        help="""Delete a reminder.""",
        brief="Delete a reminder.",
        aliases=["remove"],
        enabled=True,
        hidden=False,
    )
    async def reminder_delete_cmd(
        self, ctx: commands.Context, reminder_id: int
    ) -> None:
        """
        Delete a reminder.
        """
        reminder = await self.rm.fetch_reminder(reminder_id)
        if reminder is None:
            raise commands.BadArgument("Reminder not found")
        if reminder.uid != ctx.author.id:
            raise commands.BadArgument("You do not own this reminder")
        await self.rm.delete_reminder(reminder_id)
        embed = discord.Embed(
            title="Deleted Reminder",
            description=f">>> {reminder.reminder}",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        embed.set_footer(
            text=f"Reminder ID: {reminder.rid}",
        )
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """
    Setup the Cog.
    """
    await bot.add_cog(Reminders(bot))
