from quart import Quart
import quart
import quart_discord as qd
from discord.ext import ipc
import json


app = Quart(__name__)

config = json.load(open("config.json"))
ipc_client = ipc.Client(secret_key=config.get("IPC").get("Secret"))

app.secret_key = b"lakjhsdlkjalksjdlkajslkd"

app.config["DISCORD_CLIENT_ID"] = 889672871620780082
app.config["DISCORD_CLIENT_SECRET"] = config.get("Bot").get("Secret")
app.config["DISCORD_REDIRECT_URI"] = "http://bennybot.me/callback"
app.config["DISCORD_BOT_TOKEN"] = config.get("Bot").get("Token")

qdiscord = qd.DiscordOAuth2Session(app)


@app.route("/")
async def index():
    """Index"""
    return("Hello world")

@app.route("/members")
async def members():
    member_count = await ipc_client.request(
        "get_member_count", guild_id=839605885700669441
    )

    return str(member_count)  # display member count

@app.route("/login")
async def login():
    return await qdiscord.create_session()

@app.route("/callback/")
async def callback():
    await qdiscord.callback()
    return quart.redirect(quart.url_for(".me"))


@app.errorhandler(qd.Unauthorized)
async def redirect_unauthorized(e):
    return quart.redirect(quart.url_for("login"))

	
@app.route("/me/")
@qd.requires_authorization
async def me():
    user = await qdiscord.fetch_user()
    return f"""
    <html>
        <head>
            <title>{user.name}</title>
        </head>
        <body>
            <img src='{user.avatar_url}' />
        </body>
    </html>"""


app.run(host="0.0.0.0", port=5000)