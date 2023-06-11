import asyncio
from discord import Intents
from bot import Bot

with open("token.0", 'r', encoding="utf-8") as tf:
    token = tf.read()

with open("assets/arxiv-logo.jpg", 'rb') as pf:
    pp = pf.read()

intents = Intents.default()
intents.message_content = True

bot = Bot(intents=intents, cogs=["utils", "arxiv"], avatar=pp)
asyncio.run(bot.run(token))
