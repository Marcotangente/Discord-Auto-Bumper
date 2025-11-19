import discord
from discord.ext.commands import Bot
import os
from dotenv import load_dotenv
import disboard_embed_decoder

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

CHANNEL_ID = 1396626329129975849
TARGET_APPLICATION_ID = 302050872383242240
SLASH_COMMAND_NAME = "bump"
TARGET_BOT_ID = 302050872383242240

class MyClient(Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        channel = self.get_channel(CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            
            command_list = [
                cmd for cmd in await channel.application_commands() 
                if cmd.name == SLASH_COMMAND_NAME and cmd.application_id == TARGET_APPLICATION_ID
            ]

            if not command_list:
                print(f"Commande 'help' (ID: {TARGET_APPLICATION_ID}) non trouvée.")
                return
            
            target_command = command_list[0]

            await target_command.__call__(channel=channel)


    async def on_message(self, message: discord.Message):
        if message.channel.id != CHANNEL_ID:
            return
        
        interaction = message.interaction
        if interaction is None:
            return
        
        user = self.user
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

        await self.process_commands(message)

client = MyClient(command_prefix="?")
if DISCORD_TOKEN is not None:
    client.run(DISCORD_TOKEN)
