from quart import Quart
from discord.ext import ipc
import json


app = Quart(__name__)
config = json.load(open("config.json"))
ipc_client = ipc.Client(secret_key=config.get("IPC").get("Secret"))


@app.route("/")
async def index():
    member_count = await ipc_client.request(
        "get_member_count", guild_id=839605885700669441
    )

    return str(member_count)  # display member count


app.run()