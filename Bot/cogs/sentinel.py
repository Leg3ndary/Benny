import asyncio
import io

import aiohttp
import asqlite
import cleantext
import discord
import discord.utils
from colorama import Fore
from detoxify import Detoxify
from discord.ext import commands
from gears import style


class Toxicity:
    """
    Toxicity info for easy access

    Attributes
    ----------
    toxicity: float
        Toxic level
    severe_toxicity: float

    """

    def __init__(self, prediction: dict) -> None:
        """
        Init

        Parameters
        ----------
        prediction: dict
            The prediction dict to build the Toxicity object off of
        """
        self.toxicity = round(prediction.get("toxicity"), 5) * 100
        self.severe_toxicity = round(prediction.get("severe_toxicity"), 5) * 100
        self.obscene = round(prediction.get("obscene"), 5) * 100
        self.identity_attack = round(prediction.get("identity_attack"), 5) * 100
        self.insult = round(prediction.get("insult"), 5) * 100
        self.threat = round(prediction.get("threat"), 5) * 100
        self.sexual_explicit = round(prediction.get("sexual_explicit"), 5) * 100
        self.average = (
            round(
                self.toxicity
                + self.severe_toxicity
                + self.obscene
                + self.identity_attack
                + self.insult
                + self.threat
                + self.sexual_explicit,
                5,
            )
            / 7
        )


class SentinelConfig:
    """
    Config object
    """

    def __init__(
        self,
        channels: str,
        premium: bool,
        webhook: str,
        username: str,
        avatar: str,
        toxicity: int,
        severe_toxicity: int,
        obscene: int,
        identity_attack: int,
        insult: int,
        threat: int,
        sexual_explicit: int,
    ) -> None:
        """
        Init for config
        """
        self.channels = channels.split("-")
        self.premium = premium
        self.webhook = webhook
        self.username = username
        self.avatar = avatar
        self.toxicity = toxicity
        self.severe_toxicity = severe_toxicity
        self.obscene = obscene
        self.identity_attack = identity_attack
        self.insult = insult
        self.threat = threat
        self.sexual_explicit = sexual_explicit
        self.average = (
            toxicity
            + severe_toxicity
            + obscene
            + identity_attack
            + insult
            + threat
            + sexual_explicit
        ) / 7


class SentinelManager:
    """
    Class for managing sentinels
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        db: asqlite.Connection,
        loop: asyncio.AbstractEventLoop,
        avatar: str,
    ) -> None:
        """
        Init the sentinel manager with everything it needs
        """
        self.sentinel = Detoxify(model_type="unbiased")
        self.loop = loop
        self.db = db
        self.sentinels = {}
        self.session = session
        self.username = "Benny Sentinel"
        self.avatar = avatar

    async def process(self, msg: discord.Message) -> None:
        """
        Process a message and everything
        """
        if msg.author.bot:
            return

        sentinel = self.sentinels.get(str(msg.guild.id))
        if not sentinel or str(msg.channel.id) not in sentinel.channels:
            pass

        else:
            toxicity = await self.check(msg.clean_content)
            if (
                toxicity.toxicity > sentinel.toxicity
                or toxicity.severe_toxicity > sentinel.severe_toxicity
                or toxicity.obscene > sentinel.obscene
                or toxicity.identity_attack > sentinel.identity_attack
                or toxicity.insult > sentinel.insult
                or toxicity.threat > sentinel.threat
                or toxicity.sexual_explicit > sentinel.sexual_explicit
                or toxicity.average > sentinel.average
            ):
                webhook = discord.Webhook.from_url(
                    url=sentinel.webhook,
                    session=self.session,
                )

                values = []

                values.append(f"{toxicity.toxicity}-{sentinel.toxicity}")
                values.append(f"{toxicity.severe_toxicity}-{sentinel.severe_toxicity}")
                values.append(f"{toxicity.obscene}-{sentinel.obscene}")
                values.append(f"{toxicity.identity_attack}-{sentinel.identity_attack}")
                values.append(f"{toxicity.insult}-{sentinel.insult}")
                values.append(f"{toxicity.threat}-{sentinel.threat}")
                values.append(f"{toxicity.sexual_explicit}-{sentinel.sexual_explicit}")
                values.append(f"{toxicity.average}-{sentinel.average}")

                embed = discord.Embed(
                    title=f"Sentinel Alert",
                    description=await self.gen_toxicity_bar(values),
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.RED,
                )

                for msg in reversed(
                    [message async for message in msg.channel.history(limit=5)]
                ):
                    preview = msg.content
                    if not preview:
                        preview = "No message content."
                    elif len(msg.content) > 500:
                        preview = f"{msg.content[:497]}..."
                    embed.add_field(
                        name=f"{msg.author.name}#{msg.author.discriminator} - {msg.author.id}",
                        value=preview,
                        inline=False,
                    )
                await webhook.send(embed=embed)

    async def check(self, msg: str) -> Toxicity:
        """
        Check a message and return a toxicity class
        """
        return Toxicity(
            await self.loop.run_in_executor(None, self.sentinel.predict, msg)
        )

    async def gen_toxicity_bar(self, values: list) -> str:
        """
        Generate a nice loading bar based on the stuff we output, custom built to show progress bars
        """
        bars = []
        bars_colors = []
        for value in values:
            val1 = float(value.split("-")[0])
            val2 = float(value.split("-")[1])

            posneg = val1 > val2

            if posneg:
                bar_color = Fore.RED
            elif val1 > val2 / 2:
                bar_color = Fore.YELLOW
            else:
                bar_color = Fore.GREEN

            bar_num = round(val1 / (100 / 50))

            bars.append(
                f"""{bar_color}{bar_num * "█"}{Fore.WHITE}{(50 - bar_num) * "█"}"""
            )
            bars_colors.append(bar_color)

        view = f"""```ansi
{Fore.WHITE}Toxicity                                    {bars_colors[0]}{round(float(values[0].split("-")[0]), 2)}%
{bars[0]}
Severe Toxicity                             {bars_colors[1]}{round(float(values[1].split("-")[0]), 2)}%
{bars[1]}
Obscene                                     {bars_colors[2]}{round(float(values[2].split("-")[0]), 2)}%
{bars[2]}
Identity Attack                             {bars_colors[3]}{round(float(values[3].split("-")[0]), 2)}%
{bars[3]}
Insult                                      {bars_colors[4]}{round(float(values[4].split("-")[0]), 2)}%
{bars[4]}
Threat                                      {bars_colors[5]}{round(float(values[5].split("-")[0]), 2)}%
{bars[5]}
Sexual Explicit                             {bars_colors[6]}{round(float(values[6].split("-")[0]), 2)}%
{bars[6]}
Average                                     {bars_colors[7]}{round(float(values[7].split("-")[0]), 2)}%
{bars[7]}
```"""

        return view

    async def load_sentinels(self) -> None:
        """
        Load all sentinels objects into a cache so we can retrieve it quickly
        """
        async with self.db.cursor() as cursor:
            query = """SELECT * FROM config;"""
            data = await cursor.execute(query)
            data = await data.fetchall()
            if data:
                for config in data:
                    self.sentinels[config[0]] = SentinelConfig(
                        config[1],
                        config[2],
                        config[3],
                        config[4],
                        config[5],
                        config[6],
                        config[7],
                        config[8],
                        config[9],
                        config[10],
                        config[11],
                        config[12],
                    )

    async def load_sentinel(self, guild: str) -> None:
        """
        Load a single sentinel quickly, can be used to update old models if for some reason they didn't update
        """
        async with self.db.cursor() as cursor:
            async with await cursor.execute(
                """SELECT * FROM config WHERE guild = ?;""", (str(guild),)
            ) as data:
                config = await data.fetchone()
                self.sentinels[config[0]] = SentinelConfig(
                    config[1],
                    config[2],
                    config[3],
                    config[4],
                    config[5],
                    config[6],
                    config[7],
                    config[8],
                    config[9],
                    config[10],
                    config[11],
                    config[12],
                )

    async def save_default_config(self, ctx: commands.Context) -> None:
        """
        Generate default config
        """
        await ctx.defer()

        sentinel = self.sentinels.get(str(ctx.guild.id))

        if not sentinel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False
                ),
                ctx.guild.me: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True
                ),
            }
            channel = await ctx.guild.create_text_channel(
                "sentinel", overwrites=overwrites
            )

            async with self.session.get(self.avatar) as raw:
                avatar_bytes = io.BytesIO(await raw.content.read())

            webhook = await channel.create_webhook(
                name=self.username,
                avatar=avatar_bytes.getvalue(),
                reason="BennyBot Sentinel Webhook",
            )
            webhook_success = discord.Embed(
                title=f"Successfully created channel and webhook!",
                description=f"""Sentinel Alerts will now be sent here""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREEN,
            )
            await channel.send(embed=webhook_success)

            await self.new_guild(ctx.guild.id, ctx.channel.id, webhook.url)

            embed = discord.Embed(
                title=f"Success",
                description=f"""Set default sentinel config.""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREEN,
            )
            await ctx.send(embed=embed)

        else:
            raise commands.BadArgument(
                "You already have a sentinel config setup for this server"
            )

    async def new_guild(self, guild: str, channel: str, webhook: str) -> None:
        """
        Ensure a guild actually has a config
        """
        await self.db.execute(
            """
            INSERT INTO config VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                str(guild),
                str(channel),
                False,
                webhook,
                self.username,
                self.avatar,
                75,
                75,
                75,
                75,
                75,
                75,
                75,
            ),
        )
        await self.db.commit()
        await self.load_sentinel(guild)

    async def view_config(self, ctx: commands.Context) -> None:
        """
        View current sentinel setup for a server
        """
        sentinel = self.sentinel.get(str(ctx.guild.id))
        if not sentinel:
            raise commands.BadArgument(
                "You need to create a Sentinel config with /sentinel default!"
            )

        embed = discord.Embed(
            title=f"Sentinel Config",
            description=f"""This server is {"marked Premium" if sentinel.premium else "not marked Premium."}
            """,
            timestamp=discord.utils.utcnow(),
            color=style.Color.RED,
        )
        embed.add_field(name="Current Config", value="Stuff")
        await ctx.send(embed=embed, view=SentinelConfigView(sentinel))

    async def edit_config(self, ctx: commands.Context) -> None:
        """
        Edit config
        """
        await ctx.send_modal()


class DecancerManager:
    """
    Class for managing decancer states and info
    """

    def __init__(self, db: asqlite.Connection, avatar: str) -> None:
        """
        Init the manager
        """
        self.db = db
        self.username = "Benny Decancer"
        self.avatar = avatar

    async def ensure_guild(self, guild: int) -> None:
        """Ensure a guild is in our db, if not found, will quickly add default config"""
        async with self.db.cursor() as cur:
            check = await cur.execute(
                """SELECT guild FROM decancer WHERE guild = ?;""", (str(guild))
            )
            if not await check.fetchone():
                # second false needs to be changed later to premium
                await cur.execute(
                    f"""INSERT INTO decancer VALUES(?, ?, ?, ?, ?,?);""",
                    (str(guild), None, False, False, self.username, self.avatar),
                )
                await self.db.commit()

    async def enable(self, guild: int) -> None:
        """Enable decancering for a guild"""
        await self.ensure_guild(guild)
        async with self.db.cursor() as cur:
            await cur.execute(
                """UPDATE decancer SET decancer = ? WHERE guild = ?;""",
                (True, str(guild)),
            )
            await self.db.commit()

    async def disable(self, guild: int) -> None:
        """Disable decancering for a guild"""
        await self.ensure_guild(guild)
        async with self.db.cursor() as cur:
            await cur.execute(
                """UPDATE decancer SET decancer = ? WHERE guild = ?;""",
                (False, str(guild)),
            )
            await self.db.commit()

    async def set_webhook(self, guild: int, webhook_url: str) -> None:
        """Set a webhook"""
        await self.ensure_guild(guild)
        async with self.db.cursor() as cur:
            await cur.execute(
                """UPDATE decancer SET webhook_url = ? WHERE guild = ?;""",
                (webhook_url, str(guild)),
            )
            await self.db.commit()

    async def get_webhook(self, guild: int) -> str:
        """Get a webhook"""
        async with self.db.cursor() as cur:
            results = await cur.execute(
                """SELECT webhook_url FROM decancer WHERE guild = ?;""", (str(guild),)
            )
            return (await results.fetchone())["webhook_url"]

    async def set_user(self, guild: int, username: str, avatar: str) -> None:
        """Set a users complete info"""
        await self.ensure_guild(guild)
        async with self.db.cursor() as cur:
            await cur.execute(
                """UPDATE decancer SET username = ?, avatar = ? WHERE guild = ?;""",
                (username, avatar, str(guild)),
            )
            await self.db.commit()

    async def decancer_user(self, guild: int) -> bool:
        """Check if we should decancer a user"""
        await self.ensure_guild(guild)
        async with self.db.cursor() as cur:
            results = await cur.execute(
                """SELECT decancer FROM decancer WHERE guild = ?;""", (str(guild),)
            )
            return (await results.fetchone())["decancer"]


class SentinelConfigModal(discord.ui.Modal, title="Sentinel Config"):
    """
    Config for sentinel
    """

    def __init__(self, config: SentinelConfig) -> None:
        """
        Init"""
        super().__init__()
        self.config = config
        threshold = discord.ui.TextInput(
            label="Set your threshold values below, it should be a 2 digit long number like below (Default 75).",
            style=discord.TextStyle.long,
            placeholder="75",
            required=False,
            max_length=2,
        )
        toxicity = discord.ui.TextInput(
            label="Toxicity",
            style=discord.TextStyle.long,
            placeholder=str(self.config.toxicity),
            required=False,
            max_length=2,
        )
        severe_toxicity = discord.ui.TextInput(
            label="Severe Toxicity",
            style=discord.TextStyle.long,
            placeholder=str(self.config.severe_toxicity),
            required=False,
            max_length=2,
        )
        obscene = discord.ui.TextInput(
            label="Obscene",
            style=discord.TextStyle.long,
            placeholder=str(self.config.obscene),
            required=False,
            max_length=2,
        )
        identity_attack = discord.ui.TextInput(
            label="Identity Attack",
            style=discord.TextStyle.long,
            placeholder=str(self.config.identity_attack),
            required=False,
            max_length=2,
        )
        insult = discord.ui.TextInput(
            label="Insult",
            style=discord.TextStyle.long,
            placeholder=str(self.config.insult),
            required=False,
            max_length=2,
        )
        threat = discord.ui.TextInput(
            label="Threat",
            style=discord.TextStyle.long,
            placeholder=str(self.config.threat),
            required=False,
            max_length=2,
        )
        sexual_explicit = discord.ui.TextInput(
            label="Sexual Explicit",
            style=discord.TextStyle.long,
            placeholder=str(self.config.sexual_explicit),
            required=False,
            max_length=2,
        )
        average = discord.ui.TextInput(
            label="Average",
            style=discord.TextStyle.long,
            placeholder=str(self.config.average),
            required=False,
            max_length=2,
        )
        self.add_item(threshold)
        self.add_item(toxicity)
        self.add_item(severe_toxicity)
        self.add_item(obscene)
        self.add_item(identity_attack)
        self.add_item(insult)
        self.add_item(threat)
        self.add_item(sexual_explicit)
        self.add_item(average)

    async def verify_input(self, config: str) -> bool:
        """
        Verify that the config is actually valid
        """

    async def pull_config(self, config: str) -> SentinelConfig:
        """
        Pull a config from a config str"""

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"Success",
            description=f"""Config successfully saved""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        await interaction.response.send_message(embed=embed)


class SentinelWatcherView(discord.ui.View):
    """
    View for sentinel thingy
    """

    def __init__(self):
        """Init"""
        super().__init__()

    @discord.ui.button(label="Ban", emoji=":hammer:", style=discord.ButtonStyle.danger)
    async def ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.send("Add ban stuff idiot")

    @discord.ui.button(label="Mute", emoji=":mute:", style=discord.ButtonStyle.danger)
    async def mute(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.send("Add mute stuff here idiot")

    @discord.ui.button(
        label="warn", emoji=":warning:", style=discord.ButtonStyle.blurple
    )
    async def warn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.send("add warn stuff loser")


class SentinelConfigView(discord.ui.View):
    """
    The Sentinel Config View
    """

    def __init__(self, config: SentinelConfig, omsg: discord.Message):
        """Init"""
        super().__init__()
        self.config = config
        self.omsg = omsg

    @discord.ui.button(
        label="Update Config", emoji=":setting:", style=discord.ButtonStyle.grey
    )
    async def update_config(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.send_modal(SentinelConfigModal(self.config))

    @discord.ui.button(
        label="Update Watched Channels", emoji=":eyes:", style=discord.ButtonStyle.grey
    )
    async def update_config(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.send_modal(SentinelConfigModal(self.config))


class Sentinel(commands.Cog):
    """
    Sentinel cog, drama watcher, moderation supreme, call it what you want
    """

    def __init__(self, bot: commands.Bot):
        """Init the detoxify models and get sessions ready!"""
        self.bot = bot

    async def cog_load(self) -> None:
        """
        On cog load setup db
        """
        self.db = await asqlite.connect("Databases/sentinel.db")
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS config (
                guild           TEXT PRIMARY KEY
                                     NOT NULL,
                channels        TEXT NOT NULL,
                premium         BOOL NOT NULL,
                webhook         TEXT NOT NULL,
                username        TEXT NOT NULL,
                avatar          TEXT NOT NULL,
                toxicity        INT  NOT NULL,
                severe_toxicity INT  NOT NULL,
                obscene         INT  NOT NULL,
                identity_attack INT  NOT NULL,
                insult          INT  NOT NULL,
                threat          INT  NOT NULL,
                sexual_explicit INT  NOT NULL
            );
            """
        )
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS decancer (
                guild           TEXT NOT NULL
                                    PRIMARY KEY,
                webhook_url     TEXT,
                decancer        BOOL NOT NULL,
                premium         BOOL NOT NULL,
                username        TEXT NOT NULL,
                avatar          TEXT NOT NULL
            );
            """
        )
        await self.bot.blogger.load("Sentinel Config")

    async def clean_username(self, username: str) -> str:
        """
        Clean a username

        Parameters
        ----------
        username: str
            The username to clean

        Returns
        -------
        str
            The cleaned username
        """
        new_username = cleantext.clean(
            username,
            fix_unicode=True,
            to_ascii=True,
            lower=False,
            no_line_breaks=True,
            no_urls=True,
            no_emails=True,
            no_phone_numbers=True,
            no_numbers=False,
            no_digits=False,
            no_currency_symbols=False,
            no_punct=False,
            replace_with_url="<URL>",
            replace_with_email="<EMAIL>",
            replace_with_phone_number="<PHONE>",
            lang="en",
        )
        return new_username

    async def cog_load(self) -> None:
        """
        On cog load check if the bot had a sm and re-add if so
        """
        if hasattr(self.bot, "sentinel_manager"):
            self.sm = self.bot.sentinel_manager
            await self.load_sentinels()

        if hasattr(self.bot, "decancer_manager"):
            self.decancer = self.bot.decancer_manager

    @commands.Cog.listener()
    async def on_load_sentinel_managers(self) -> None:
        """Load decancer manager when bots loaded"""
        self.sm = SentinelManager(
            self.bot.sessions.get("sentinel"),
            self.db,
            self.bot.loop,
            self.bot.user.avatar.url,
        )
        self.bot.sentinel_manager = self.sm
        await self.sm.load_sentinels()

        self.decancer = DecancerManager(self.db, self.bot.user.avatar.url)
        self.bot.decancer_manager = self.decancer

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        """
        Sentinels time :)
        """
        await self.sm.process(msg)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        On member join check if we have to decancer the user
        """
        check = await self.decancer.decancer_user(member.guild.id)
        if check:
            webhook_url = await self.decancer.get_webhook(member.guild.id)
            new_nick = await self.clean_username(member.display_name)

            original = member.display_name

            if new_nick != original:
                await member.edit(nick=new_nick)

            if webhook_url:
                embed = discord.Embed(
                    title=f"Decancer Automatic Action",
                    description=f"""{original} >> **{new_nick}**""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.BLUE,
                )
                embed.set_footer(text=member.id, icon_url=member.display_avatar.url)
                webhook = discord.Webhook.from_url(
                    url=webhook_url, session=self.session
                )
                await webhook.send(embed=embed)

    @commands.hybrid_group(
        name="sentinel",
        description="""View sentinel config""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def sentinel_cmd(self, ctx: commands.Context) -> None:
        """
        Sentinel command, very cool
        """

    @sentinel_cmd.command(
        name="default",
        description="""Set default command config""",
        help="""Set sentinel config to default values.""",
        brief="Use this to setup sentinel config to it's default values",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def sentinel_default_cmd(self, ctx: commands.Context) -> None:
        """Set default command config"""
        await self.sm.save_default_config(ctx)

    @sentinel_cmd.command(
        name="config",
        description="""View and edit sentinel config""",
        help="""Set sentinel config to whatever you want""",
        brief="View sentinel config values",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def sentinel_config_cmd(self, ctx: commands.Context) -> None:
        """View and edit sentinel config"""
        await self.sm.send_config(ctx)

    @commands.hybrid_group()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def decancer(self, ctx: commands.Context) -> None:
        """
        Decancer hybrid_group
        """
        if not ctx.invoked_subcommand:
            pass

    @decancer.command(
        name="enable",
        description="""Enable decancering for the server""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def decancer_enable_cmd(self, ctx: commands.Context) -> None:
        """Enable decancer"""
        await self.decancer.enable(ctx.message.guild.id)
        embed = discord.Embed(
            title=f"Enabled Decancer",
            description=f"""Successfully enabled the Decancer feature for {ctx.guild.name}.""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        embed.set_footer(
            text="Consider enabling the decancer logs feature to see how nicknames are being decancered",
            icon_url=ctx.guild.icon.url,
        )
        await ctx.send(embed=embed)

    @decancer.command(
        name="disable",
        description="""Disable the decancer feature""",
        help="""Disable the decancer feature""",
        brief="Disable the decancer feature",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def decancer_disable_cmd(self, ctx: commands.Context) -> None:
        """Disable decancer"""
        await self.decancer.disable(ctx.message.guild.id)
        embed = discord.Embed(
            title=f"Disabled Decancer",
            description=f"""Successfully enabled the Decancer feature for {ctx.guild.name}.""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.RED,
        )
        embed.set_footer(
            text="Consider re-enabling this feature!", icon_url=ctx.guild.icon.url
        )
        await ctx.send(embed=embed)

    @decancer.command(
        name="logs",
        description="""Set the decancer logs channel""",
        help="""Set the decancer logs channel""",
        brief="Set the decancer logs channel",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def decancer_logs_cmd(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        """Set the decancer logs channel"""
        old_webhook = await self.decancer.get_webhook(ctx.message.guild.id)

        if not channel:
            channel = ctx.message.channel
        if old_webhook:
            await discord.Webhook.from_url(
                url=old_webhook, session=self.session
            ).delete(reason="Removed BennyBot Decancer Logs Webhook")

        async with self.session.get(self.decancer.avatar) as raw:
            avatar_bytes = io.BytesIO(await raw.content.read())

        webhook = await channel.create_webhook(
            name=self.decancer.username,
            avatar=avatar_bytes.getvalue(),
            reason="BennyBot Decancer Logs Webhook",
        )
        await self.decancer.set_webhook(ctx.message.guild.id, webhook.url)
        embed = discord.Embed(
            title=f"Decancer Logs Channel Updated",
            description=f"""Set Decancer Logs to {channel.mention}""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN,
        )
        if not await self.decancer.decancer_user(ctx.message.guild.id):
            embed.set_footer(
                text="Reminder: You need to enable the decancer feature!",
                icon_url=ctx.guild.icon.url,
            )
        await ctx.send(embed=embed)

    @decancer.command(
        name="auto",
        description="""Automatically configure the decancer feature""",
        help="""Automatically configure the decancer feature""",
        brief="Auto setup the decancer feature",
        aliases=[],
        enabled=False,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.guild)
    async def decancer_auto_cmd(self, ctx: commands.Context) -> None:
        """Automatically configure the decancer feature"""
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(
                read_messages=False, send_messages=False
            ),
        }
        channel = await ctx.guild.create_text_channel(
            "decancer-logs", overwrites=overwrites
        )

        # ill finish this later because I really don't want to do it now

    @decancer.command(
        name="user",
        description="""Decancer a user""",
        help="""Decancer a user""",
        brief="Decancer a user",
        aliases=[],
        enabled=True,
        hidden=False,
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def decancer_user_cmd(self, ctx: commands.Context, user: discord.Member):
        """Decancer a discord user"""
        webhook_url = await self.decancer.get_webhook(ctx.message.guild.id)
        new_nick = await self.clean_username(user.display_name)

        original = user.display_name

        if new_nick != original:
            await user.edit(nick=new_nick)

        embed = discord.Embed(
            title=f"Decancer Action",
            description=f"""{original} >> **{new_nick}**""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.BLUE,
        )
        embed.set_footer(text=user.id, icon_url=user.display_avatar.url)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)

        if webhook_url:
            webhook = discord.Webhook.from_url(url=webhook_url, session=self.session)
            await webhook.send(embed=embed)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Sentinel(bot))
