import discord
import os
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.author != client.user:
            return

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')

client = MyClient()
client.run(DISCORD_TOKEN)