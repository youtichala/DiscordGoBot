import discord
import src.go
import functions.util
from bot_token import key
import config

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

async def go_action(message, content):
    if await src.go.is_go_action(message, content):
        return True
    else:
        return False

@client.event
async def on_ready():
    print('目前登入身份：', client.user)


@client.event
async def on_message(message):

    if message.author == client.user:
        return
    else:
        msgs = functions.util.str_split(message.content, ' ')
        if len(msgs) > 0:
            if len(msgs[0]) > 0:
                if msgs[0][0] == config.prefix:
                    await go_action(message, msgs[0][1::].rstrip())

try:
    client.run(key)
finally:
    pass
