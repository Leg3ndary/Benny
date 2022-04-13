from re import L
import asqlite
import asyncio
import discord
import discord.utils
from discord.ext import commands
from gears import style
from threading import Timer


"""
Reminder Schema

id - user.id of user who created this reminder
rid - Reminder id given to every reminder
datetime - The datetime to send this reminder at
reminder - The actual reminder
"""

class ReminderManager:
    """
    Reminder Task Manager
    
    Attributes
    ----------
    REMINDER_LIMIT: const
        The reminder limit for a base user
    bot: obj
        Bot instance
    remind_id: int
        Reminder ID
    active_reminders: dict
        A dict containing all active reminders formatted with the reminder id as a str
        
    Methods
    -------
    async create_table -> None
        No Params

        Simply creates a table if I decide to delete it whoops
    
    async load_config -> None
        No Params
        
        Loads config from redis and if not found initiates it

    async load_timers -> None
        No Params

        Load up all our reminders our timers as we call them here
    """

    def __init__(self, bot) -> None:
        """Constructs all the necessary attributes for our Reminder Manager"""
        self.REMINDER_LIMIT = 10
        self.bot = bot
        self.remind_id = None
        self.active_reminders = {}

    async def create_table(self) -> None:
        """Create a table for our stuff :D"""
        async with asqlite.connect("Databases/reminders.db") as db:
            schema = """CREATE reminders IF NOT EXISTS (
                rid       INTEGER       NOT NULL
                                        PRIMARY KEY,
                id        TEXT    NOT NULL,
                datetime  DATETIME   NOT NULL,
                reminder  TEXT
            );
            """
            await db.execute(schema)

    async def load_config(self) -> None:
        """Start setting up the config for the reminders"""
        self.remind_id = await self.bot.redis.get("Reminder_Count")
        if not self.remind_id:
            await self.bot.redis.set("Reminder_Count", "1")
            self.remind_id = 1
        else:
            self.remind_id = int(self.remind_id)

    async def load_timers(self) -> None:
        """Load all our reminders and timers and queue them when the bot is started so reminders actually get sent"""
        await self.load_config()
        await self.create_table()

        async with asqlite.connect("Databases/reminders.db") as db:
            query = """SELECT * FROM reminders;"""
            async with db.execute(query) as conn:
                results = await conn.fetchall()

        for reminder in results:
            await self.create_timer(reminder[0], reminder[1])


    async def create_timer(self, rid: int, uid: str, time, reminder: str) -> None:
        """Create a timer and dispatch.
        Timer id in active_reminders is rid-uid"""
        timer = asyncio.create_task(self.bot.dispatch("on_create_timer"), rid, id, time, reminder)
        async with asqlite.connect("Databases/reminders.db") as db:
            query = """INSERT INTO reminders VALUES(?, ?, 0, "");"""
            await db.execute(query, )
            await db.commit()
        self.active_reminders.update(f"{rid}-{uid}", timer)


class Reminders(commands.Cog):
    """Cog Example Description"""

    def __init__(self, bot):
        self.bot = bot
        self.rm = ReminderManager(bot)

    async def cog_load(self):
        """Dispatch to start load reminders"""
        
        #await self.rm.load_timers()

    @commands.Cog.listener()
    async def on_send_reminder(self, uid: int, reminder: str):
        """Send a reminder to a person, we use dispatch to quickly dispatch this"""
        try:
            self.bot.get_user(int(uid))
        except:
            pass
        

    @commands.command(
        name="remind",
        description="""Uses a task manager to create, send, limit, reminders.""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=["rm"],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def reminder_cmd(self, ctx):
        """Command description"""
        await self.rm.create_timer()


async def setup(bot):
    await bot.add_cog(Reminders(bot))