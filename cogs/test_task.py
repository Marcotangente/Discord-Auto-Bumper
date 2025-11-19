from discord.ext import tasks, commands
from discord.ext.commands import Bot
import disboard_embed_decoder
import discord
import asyncio

CHANNEL_ID = 1396626329129975849
TARGET_APPLICATION_ID = 302050872383242240
SLASH_COMMAND_NAME = "bump"
TARGET_BOT_ID = 302050872383242240

class TestTask(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.channel = bot.get_channel(CHANNEL_ID)
        self.loooop.start()

    def cog_unload(self):
        self.loooop.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != CHANNEL_ID:
            return
        
        interaction = message.interaction
        if interaction is None:
            return
        
        user = self.bot.user
        guild = message.guild
        if interaction.name != SLASH_COMMAND_NAME or user is None or guild is None or interaction.user.id != user.id:
            return

        # message.flags.ephemeral

        embeds = message.embeds
        if embeds:
            embed = embeds[0]
            if disboard_embed_decoder.is_success_embed(embed, guild.id):
                print("okkk")
                pass # TODO jsp
            else:
                remaining_time = disboard_embed_decoder.find_time_left(embed)
                print(remaining_time)

        await self.bot.process_commands(message)

    @tasks.loop(seconds=10.0)
    async def loooop(self):
        if isinstance(self.channel, discord.TextChannel):
            
            command_list = [
                cmd for cmd in await self.channel.application_commands() 
                if cmd.name == SLASH_COMMAND_NAME and cmd.application_id == TARGET_APPLICATION_ID
            ]

            if not command_list:
                print(f"Commande 'help' (ID: {TARGET_APPLICATION_ID}) non trouvée.")
                return
            
            target_command = command_list[0]

            await target_command.__call__(channel=self.channel)