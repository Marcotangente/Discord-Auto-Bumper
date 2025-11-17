from discord.ext import tasks, commands
from discord.ext.commands import Bot
import discord

CHANNEL_ID = 947101700697755700

class TestTask(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.channel = bot.get_channel(CHANNEL_ID)
        self.loooop.start()

    def cog_unload(self):
        self.loooop.cancel()

    @tasks.loop(seconds=5.0)
    async def loooop(self):
        print("yo")
        if isinstance(self.channel, discord.TextChannel):
            command = [_ for _ in await self.channel.application_commands() if _.name == 'help' and _.application_id == 159985415099514880][0]
            await command.__call__(channel=self.channel) 

        else:
            print(self.channel)