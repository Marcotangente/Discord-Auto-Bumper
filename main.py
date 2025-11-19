import discord
from discord.ext.commands import Bot
import os
from dotenv import load_dotenv
from cogs.test_task import TestTask

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

class MyClient(Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        await self.add_cog(TestTask(self))


client = MyClient(command_prefix="?")
if DISCORD_TOKEN is not None:
    client.run(DISCORD_TOKEN)
