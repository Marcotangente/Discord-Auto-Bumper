import asyncio
import os
import discord
from discord.ext.commands import Bot

from .disboard_embed_decoder import is_success_embed, find_time_left

TARGET_APPLICATION_ID = 302050872383242240
SLASH_COMMAND_NAME = "bump"
TARGET_BOT_ID = 302050872383242240

class BumperSelfbot(Bot):
    def __init__(self, channel_id, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.channel_id = channel_id

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        channel = self.get_channel(self.channel_id)
        if isinstance(channel, discord.TextChannel):
            
            command_list = [
                cmd for cmd in await channel.application_commands() 
                if cmd.name == SLASH_COMMAND_NAME and cmd.application_id == TARGET_APPLICATION_ID
            ]

            if not command_list:
                print(f"Commande {SLASH_COMMAND_NAME} (ID: {TARGET_APPLICATION_ID}) non trouvée.")
                return

            target_command = command_list[0]

            await target_command.__call__(channel=channel)


    async def on_message(self, message: discord.Message):
        if message.channel.id != self.channel_id:
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
            if is_success_embed(embed, guild.id):
                print("okkk")
                pass # TODO jsp
            else:
                remaining_time = find_time_left(embed)
                print(remaining_time)

        await self.process_commands(message)
        self.loop.create_task(self.shutdown())

    async def shutdown(self):
        await asyncio.sleep(1) 
        os._exit(0)


def run_bump_task(token, channel_id):
    client = BumperSelfbot(channel_id=channel_id, command_prefix="?")
    client.run(token)
