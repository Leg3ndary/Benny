import aiohttp
import asyncio
import discord
import datetime
import discord.utils
from discord.ext import commands
from gears import style
from typing_extensions import Self


class Page:
    """
    Discord summary page response
    """
    
    def __init__(self) -> None:
        """
        Discord summary, page attribute
        """
        self.id = None
        self.name = None
        self.url = None
        self.updated_at = None

    def from_data(self, data: dict) -> Self:
        """Construct the class from some data"""
        self.id = data.get("id")
        self.name = data.get("name")
        self.url = data.get("url")
        self.updated_at = datetime.datetime.fromisoformat(data.get("updated_at"))
        return self

class Status:
    """
    Discord summary status response
    """
    
    def __init__(self) -> None:
        """
        Discord summary, status attribute
        """
        self.description = None
        self.indicator = None

    def from_data(self, data: dict) -> Self:
        """Construct the class from data"""
        self.description = data.get("description")
        self.indicator = data.get("indicator")
        return self

class Component:
    """Summary components, can have multiple"""

    def __init__(self) -> None:
        """
        Init the component class
        """
        self.created_at = None
        self.description = None
        self.id = None
        self.name = None
        self.page_id = None
        self.position = None
        self.status = None
        self.updated_at = None

    def from_data(self, data: dict) -> Self:
        """Construct the class from data"""
        self.created_at = datetime.datetime.fromisoformat(data.get("created_at"))
        self.description = data.get("description")
        self.id = data.get("id")
        self.name = data.get("name")
        self.page_id = data.get("page_id")
        self.position = data.get("position")
        self.status = data.get("status")
        self.updated_at = datetime.datetime.fromisoformat(data.get("updated_at"))
        return self

class Incident:
    """
    Summary incident class
    """
    
    def __init__(self) -> None:
        """
        Init the incident class with atributes
        """
        self.created_at = None
        self.id = None
        self.impact = None
        self.incident_updates = []
        self.monitoring_at = None
        self.name = None
        self.page_id = None
        self.resolved_at = None
        self.shortlink = None
        self.status = None
        self.updated_at = None

    def from_data(self, data: dict) -> Self:
        """Construct the class from data"""
        self.created_at = datetime.datetime.fromisoformat(data.get("created_at"))
        self.id = data.get("id")
        self.impact = data.get("impact")
        if data.get("incident_updates"):
            for incident_update in data.get("incident_updates"):
                self.incident_updates.append(IncidentUpdate().from_data(incident_update))
        self.monitoring_at = datetime.datetime.fromisoformat(data.get("monitoring_at"))
        self.name = data.get("name")
        self.page_id = data.get("page_id")
        self.resolved_at = datetime.datetime.fromisoformat(data.get("resolved_at"))
        self.shortlink = data.get("shortlink")
        self.status = data.get("status")
        self.updated_at = datetime.datetime.fromisoformat(data.get("updated_at"))
        return self

class IncidentUpdate:
    """Summary incident update class"""
    
    def __init__(self) -> None:
        """Summary incident update init"""
        self.body = None
        self.created_at = None
        self.display_at = None
        self.id = None
        self.incident_id = None
        self.status = None
        self.updated_at = None

    def from_data(self, data: dict) -> Self:
        """Construct the class from data"""
        self.body = data.get("body")
        self.created_at = datetime.datetime.fromisoformat(data.get("created_at"))
        self.display_at = datetime.datetime.fromisoformat(data.get("display_at"))
        self.id = data.get("id")
        self.incident_id = data.get("incident_id")
        self.status = data.get("status")
        self.updated_at = datetime.datetime.fromisoformat(data.get("updated_at"))
        return self

class ScheduledMaintenance:
    """
    A Scheduled Maintenance
    """
    
    def __init__(self) -> None:
        """init the scheduled maintenance class"""
        self.created_at = None
        self.id = None
        self.impact = None
        self.incident_updates = []
        self.monitoring_at = None
        self.name = None
        self.page_id = None
        self.resolved_at = None
        self.scheduled_for = None
        self.scheduled_until = None
        self.shortlink = None
        self.status = None
        self.updated_at = None

    def from_data(self, data: dict) -> Self:
        """Generate the class data from a dict"""
        self.created_at = datetime.datetime.fromisoformat(data.get("created_at"))
        self.id = data.get("id")
        self.impact = data.get("impact")
        if data.get("incident_updates"):
            for incident_update in data.get("incident_updates"):
                self.incident_updates.append(IncidentUpdate().from_data(incident_update))
        self.monitoring_at = datetime.datetime.fromisoformat(data.get("monitoring_at"))
        self.name = data.get("name")
        self.page_id = data.get("page_id")
        self.resolved_at = datetime.datetime.fromisoformat(data.get("resolved_at"))
        self.scheduled_for = datetime.datetime.fromisoformat(data.get("scheduled_for"))
        self.scheduled_until = datetime.datetime.fromisoformat(data.get("scheduled"))
        self.shortlink = data.get("shortlink")
        self.status = data.get("status")
        self.updated_at = datetime.datetime.fromisoformat(data.get("updated_at"))
        return self

class Summary:
    """
    Discord summary response class
    """

    def __init__(self) -> None:
        """
        Init the data class
        """
        self.page = Page()
        self.status = Status()
        self.components = []
        self.incidents = []
        self.scheduled_maintenances = []
    
    def from_data(self, data: dict) -> Self:
        """
        Construct a summary object from data
        """
        self.page.from_data(data.get("page"))
        self.status.from_data(data.get("status"))
        if data.get("components"):
            for component in data.get("components"):
                self.components.append(Component().from_data(component))
        if data.get("incidents"):
            for incident in data.get("incidents"):
                self.incidents.append(Incident().from_data(incident))
        if data.get("scheduled_maintenances"):
            for scheduled_maintenance in data.get("scheduled_maintenances"):
                self.scheduled_maintenances.append(ScheduledMaintenance().from_data(scheduled_maintenance))
        return self


class DiscordStatusClient:
    """A client for accessing info about discord status"""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Init the client"""
        self.session = session
        self.api_url = "https://discordstatus.com/api/v2"
        self.cache = {
            "summary": {
                "data": None,
                "last_fetched": 0
            }
        }

    async def get_summary(self) -> Summary:
        """
        To limit overall requests to the api, this will save the latest object and only request
        a new object if it's been over 3000 seconds (5 Minutes)
        """
        if round(datetime.datetime.now().timestamp()) > self.cache["summary"]["last_fetched"] + 3000:
            self.cache["summary"]["data"] = await self.fetch_summary()
            print(self.cache["summary"]["data"])
            self.cache["summary"]["last_fetched"] = round(datetime.datetime.now().timestamp())

        return self.cache["summary"]["data"]

    async def fetch_summary(self) -> Summary:
        """
        Fetch a summary of the api's status
        """
        async with self.session.get(f"{self.api_url}/summary.json") as resp:
            if resp.status == 200:
                json = await resp.json()
                data = Summary().from_data(json)
                print(data)
                return data
            raise DSException(f"{resp.status} {await resp.json()}")


class DSException(Exception):
    """
    Raised when we have an exception for DiscordStatusClass, shouldn't ever really happen
    """

    pass


class SummaryView(discord.ui.View):
    """
    Class for viewing a discord summary
    """
    pass


class DiscordStatus(commands.Cog):
    """Discord Status, not done"""

    def __init__(self, bot: commands.Bot) -> None:
        """init the discordstatus"""
        self.bot = bot
        self.dsc = DiscordStatusClient(self.bot.sessions.get("discordstatus"))

    @commands.hybrid_group(
        name="discord",
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def discord_group(self, ctx: commands.Context) -> None:
        """Discord group"""
        pass

    @discord_group.command(
        name="summary",
        description=f"""Show a summary of stuff discord's been doing""",
        help="""Show what discord's been doing lately""",
        brief="Discord Status Summary",
        aliases=[],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def discord_summary_cmd(self, ctx: commands.Context) -> None:
        """Discord summary"""
        summary = await self.dsc.get_summary()
        embed = discord.Embed(
            title=f"{summary.page.name} - {summary.page.id}",
            url=summary.page.url,
            description=f"""Last updated: <t:{round(summary.page.updated_at.timestamp())}:F> (<t:{round(summary.page.updated_at.timestamp())}:R>)""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.AQUA
        )
        embed.add_field(
            name=f"Status - {summary.status.indicator}",
            value=summary.status.description,
        )
        embed.add_field
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DiscordStatus(bot))
