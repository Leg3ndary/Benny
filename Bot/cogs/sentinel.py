import asqlite
import discord
import discord.utils
from discord.ext import commands
from gears import style
from detoxify import Detoxify
import io
import cleantext


class DecancerManager:
    """
    Class for managing decancer states and info
    """

    def __init__(self, db, avatar) -> None:
        """
        Init the manager
        """
        self.db = db
        self.username = "Benny Decancer"
        self.avatar = avatar

    async def ensure_guild(self, guild: int) -> None:
        """Ensure a guild is in our db, if not found, will quickly add default config"""
        async with self.db.cursor() as cur:
            check = await cur.execute("""SELECT guild FROM decancer WHERE guild = ?;""", (str(guild)))
            if not await check.fetchone():
                # second false needs to be changed later to premium
                await cur.execute(f"""INSERT INTO decancer VALUES(?, ?, ?, ?, ?,?);""", (str(guild), None, False, False, self.username, self.avatar))
                await self.db.commit()
    
    async def enable(self, guild: int) -> None:
        """Enable decancering for a guild"""
        await self.ensure_guild(guild)
        async with self.db.cursor() as cur:
            await cur.execute("""UPDATE decancer SET decancer = ? WHERE guild = ?;""", (True, str(guild)))
            await self.db.commit()
    
    async def disable(self, guild: int) -> None:
        """Disable decancering for a guild"""
        await self.ensure_guild(guild)
        async with self.db.cursor() as cur:
            await cur.execute("""UPDATE decancer SET decancer = ? WHERE guild = ?;""", (False, str(guild)))
            await self.db.commit()

    async def set_webhook(self, guild: int, webhook_url: str) -> None:
        """Set a webhook"""
        await self.ensure_guild(guild)
        async with self.db.cursor() as cur:
            await cur.execute("""UPDATE decancer SET webhook_url = ? WHERE guild = ?;""", (webhook_url, str(guild)))
            await self.db.commit()

    async def get_webhook(self, guild: int) -> str:
        """Get a webhook"""
        async with self.db.cursor() as cur:
            results = await cur.execute("""SELECT webhook_url FROM decancer WHERE guild = ?;""", (str(guild),))
            return (await results.fetchone())["webhook_url"]

    async def set_user(self, guild: int, username: str, avatar: str) -> None:
        """Set a users complete info"""
        await self.ensure_guild(guild)
        async with self.db.cursor() as cur:
            await cur.execute("""UPDATE decancer SET username = ?, avatar = ? WHERE guild = ?;""", (username, avatar, str(guild)))
            await self.db.commit()

    async def decancer_user(self, guild: int) -> bool:
        """Check if we should decancer a user"""
        await self.ensure_guild(guild)
        async with self.db.cursor() as cur:
            results = await cur.execute("""SELECT decancer FROM decancer WHERE guild = ?;""", (str(guild),))
            return (await results.fetchone())["decancer"]


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
            (
                self.toxicity
                + self.severe_toxicity
                + self.obscene
                + self.identity_attack
                + self.insult
                + self.threat
                + self.sexual_explicit
            )
            / 7
        ) * 100


class Config:
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
            self.toxicity
            + self.severe_toxicity
            + self.obscene
            + self.identity_attack
            + self.insult
            + self.threat
            + self.sexual_explicit
        ) / 7


class SentinelConfigModal(discord.ui.Modal, title="Sentinel Config"):
    """
    Config for sentinel
    """

    config = discord.ui.TextInput(
        label="Set config below, please only change the numbers",
        style=discord.TextStyle.long,
        placeholder="Type your feedback here...",
        required=True,
        max_length=500,
    )

    async def verify_input(self, config: str) -> bool:
        """
        Verify that the config is actually valid
        """

    async def pull_config(self, config: str) -> Config:
        """
        Pull a config from a config str"""

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"",
            description=f"""""",
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

    def __init__(self):
        """Init"""
        super().__init__()

    @discord.ui.button(
        label="Update Config", emoji=":setting:", style=discord.ButtonStyle.grey
    )
    async def update_config(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.send_modal(SentinelConfigModal())


class Sentinel(commands.Cog):
    """
    Sentinel cog, drama watcher, moderation supreme, call it what you want
    """

    def __init__(self, bot):
        self.bot = bot
        self.sentinel = Detoxify(model_type="unbiased")
        self.sentinels = {}
        self.session = bot.sensession

    async def cog_load(self) -> None:
        """
        On cog load setup db
        """
        self.db = await asqlite.connect("Databases/sentinel.db")
        async with self.db.cursor() as cur:
            await cur.execute(
                """
                CREATE TABLE IF NOT EXISTS config (
                    guild           TEXT NOT NULL
                                        PRIMARY KEY,
                    channels        TEXT,
                    premium         BOOL NOT NULL,
                    webhook_url     TEXT NOT NULL,
                    username        TEXT,
                    avatar          TEXT,
                    webhook         INT NOT NULL,
                    toxicity        INT NOT NULL,
                    severe_toxicity INT NOT NULL,
                    obscene         INT NOT NULL,
                    identity_attack INT NOT NULL,
                    insult          INT NOT NULL,
                    threat          INT NOT NULL,
                    sexual_explicit INT NOT NULL
                );
                """
            )
            await cur.execute(
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
        await self.bot.printer.p_load("Sentinel Config")

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
        new_username = cleantext.clean(username,
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
            lang="en"
        )
        return new_username

    async def load_sentinels(self) -> None:
        """
        Load all sentinels objects into a cache so we can retrieve it quickly
        """
        async with self.db.cursor() as cursor:
            query = """SELECT * FROM config;"""
            data = await cursor.execute(query)
            if data:
                for config in data:
                    self.sentinels[config[0]] = Config(
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
                        config[13],
                    )

    async def sentinel_check(self, msg: str) -> Toxicity:
        """
        Check for toxification
        """
        return Toxicity(self.sentinel.predict(msg))

    @commands.Cog.listener()
    async def on_load_decancer_manager(self) -> None:
        """Load decancer manager when bots loaded"""
        self.decancer = DecancerManager(self.db, self.bot.user.avatar.url)

    @commands.Cog.listener()
    async def on_message(self, msg):
        """
        Sentinels time :)
        """
        if msg.author.bot:
            return
        sentinel = self.sentinels.get(str(msg.guild.id))
        if not sentinel or msg.channel.id not in sentinel.channels:
            pass
        else:
            toxicness = await self.sentinel_check(msg.clean_content)
            if (
                toxicness.toxicity > sentinel.toxicity
                or toxicness.severe_toxicity > sentinel.severe_toxicity
                or toxicness.obscene > sentinel.obscene
                or toxicness.identity_attack > sentinel.identity_attack
                or toxicness.insult > sentinel.insult
                or toxicness.threat > sentinel.threat
                or toxicness.sexual_explicit > sentinel.sexual_explicit
                or toxicness.average > sentinel.average
            ):
                webhook = discord.Webhook.from_url(
                    sentinel.webhook_url,
                    adapter=discord.AsyncWebhookAdapter(self.session),
                )
                embed = discord.Embed(
                    title=f"Are you being toxic?",
                    description=f"""So rude.
                    toxicity: {toxicness.toxicity}%
                    severe_toxicity: {toxicness.severe_toxicity}
                    obscene: {toxicness.obscene}
                    identity_attack: {toxicness.identity_attack}
                    insult: {toxicness.insult}
                    threat: {toxicness.threat}
                    sexual_explicit: {toxicness.sexual_explicit}
                    average: {toxicness.average}""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.RED,
                )
                await webhook.send(embed=embed)

        '''
        if msg.author.bot:
            pass
        elif msg.guild.id == 839605885700669441:
            toxic = await self.sentinel_check(msg.clean_content)
            if toxic.toxicity > 0.6:
                
                await msg.channel.send(embed=embed, delete_after=10)
        '''

    @commands.Cog.listener()
    async def on_member_join(self, member) -> None:
        """
        On member join check if we have to decancer the user
        """
        check = await self.decancer.decancer_user(member.guild.id)
        if check:
            webhook_url = await self.decancer.get_webhook(member.guild.id)
            new_nick = await self.clean_username(member.display_name)

            original = member.display_name

            if new_nick != original:
                await member.edit(
                    nick=new_nick
                )

            if webhook_url:
                embed = discord.Embed(
                    title=f"Decancer Automatic Action",
                    description=f"""{original} >> **{new_nick}**""",
                    timestamp=discord.utils.utcnow(),
                    color=style.Color.random()
                )
                embed.set_footer(
                    text=member.id,
                    icon_url=member.display_avatar.url
                )
                webhook = discord.Webhook.from_url(
                    url=webhook_url,
                    session=self.session
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
    async def sentinel_cmd(self, ctx):
        """
        Sentinel command, very cool
        """
        embed = discord.Embed(
            title=f"Sentinel Config",
            description=f"""
            """,
            timestamp=discord.utils.utcnow(),
            color=style.Color.RED,
        )
        embed.add_field(name="Current Config", value="Stuff")
        await ctx.send(embed=embed, view=SentinelConfigView())

    @sentinel_cmd.command(
        name="default",
        description="""Set default command config""",
        help="""Set sentinel config to default values.""",
        brief="You should also use this to setup",
        aliases=[],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def sentinel_default_cmd(self, ctx):
        """Set default command config"""

    @commands.hybrid_group()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def decancer(self, ctx):
        """
        Decancer hybrid_group
        """

    @decancer.command(
        name="enable",
        description="""Enable decancering for the server""",
        help="""What the help command displays""",
        brief="Brief one liner about the command",
        aliases=[],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def decancer_enable_cmd(self, ctx):
        """Enable decancer"""
        await self.decancer.enable(ctx.message.guild.id)
        embed = discord.Embed(
            title=f"Enabled Decancer",
            description=f"""Successfully enabled the Decancer feature for {ctx.guild.name}.""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.GREEN
        )
        embed.set_footer(
            text="Consider enabling the decancer logs feature to see how nicknames are being decancered",
            icon_url=ctx.guild.icon.url
        )
        await ctx.send(embed=embed)

    @decancer.command(
        name="disable",
        description="""Disable the decancer feature""",
        help="""Disable the decancer feature""",
        brief="Disable the decancer feature",
        aliases=[],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def decancer_disable_cmd(self, ctx):
        """Disable decancer"""
        await self.decancer.disable(ctx.message.guild.id)
        embed = discord.Embed(
            title=f"Disabled Decancer",
            description=f"""Successfully enabled the Decancer feature for {ctx.guild.name}.""",
            timestamp=discord.utils.utcnow(),
            color=style.Color.RED
        )
        embed.set_footer(
            text="Consider re-enabling this feature!",
            icon_url=ctx.guild.icon.url
        )
        await ctx.send(embed=embed)

    @decancer.command(
        name="logs",
        description="""Set the decancer logs channel""",
        help="""Set the decancer logs channel""",
        brief="Set the decancer logs channel",
        aliases=[],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def decancer_logs_cmd(self, ctx, channel: discord.TextChannel = None):
        """Set the decancer logs channel"""
        old_webhook = await self.decancer.get_webhook(ctx.message.guild.id)

        if not channel:
            channel = ctx.message.channel
        if old_webhook:
            await discord.Webhook.from_url(
                url=old_webhook,
                session=self.session
            ).delete(
                reason="Removed BennyBot Decancer Logs Webhook"
            )

        async with self.session.get(self.decancer.avatar) as raw:
            avatar_bytes = io.BytesIO(await raw.content.read())

            webhook = await channel.create_webhook(
                name=self.decancer.username,
                avatar=avatar_bytes.getvalue(),
                reason="BennyBot Decancer Logs Webhook"
            )
            await self.decancer.set_webhook(ctx.message.guild.id, webhook.url)
            embed = discord.Embed(
                title=f"Decancer Logs Channel Updated",
                description=f"""Set Decancer Logs to {channel.mention}""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.GREEN
            )
            if not await self.decancer.decancer_user(ctx.message.guild.id):
                embed.set_footer(
                    text="Reminder: You need to enable the decancer feature!",
                    icon_url=ctx.guild.icon.url
                )
            await ctx.send(embed=embed)

    @decancer.command(
        name="auto",
        description="""Automatically configure the decancer feature""",
        help="""Automatically configure the decancer feature""",
        brief="Auto setup the decancer feature",
        aliases=[],
        enabled=False,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.guild)
    async def decancer_auto_cmd(self, ctx):
        """Automatically configure the decancer feature"""
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(
                read_messages=False,
                send_messages=False
            ),
        }
        channel = await ctx.guild.create_text_channel("decancer-logs", overwrites=overwrites)

        # ill finish this later because I really don't want to do it now

    @decancer.command(
        name="user",
        description="""Decancer a user""",
        help="""Decancer a user""",
        brief="Decancer a user",
        aliases=[],
        enabled=True,
        hidden=False
    )
    @commands.cooldown(1.0, 5.0, commands.BucketType.user)
    async def decancer_user_cmd(self, ctx, user: discord.Member):
        """Decancer a discord user"""
        webhook_url = await self.decancer.get_webhook(ctx.message.guild.id)
        new_nick = await self.clean_username(user.display_name)

        original = user.display_name

        if new_nick != original:
            await user.edit(
                nick=new_nick
            )

        if webhook_url:
            embed = discord.Embed(
                title=f"Decancer Automatic Action",
                description=f"""{original} >> **{new_nick}**""",
                timestamp=discord.utils.utcnow(),
                color=style.Color.random()
            )
            embed.set_footer(
                text=user.id,
                icon_url=user.display_avatar.url
            )
            webhook = discord.Webhook.from_url(
                url=webhook_url,
                session=self.session
            )
            await webhook.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Sentinel(bot))
