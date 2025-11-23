import multiprocessing
import os
import discord
from discord.ext import commands
import asyncio
from typing import Callable, Any

class InfoResolver(commands.Bot):
    task_callback: Callable[[Any], Any]
    task_context: Any
    result_queue: multiprocessing.Queue

    def __init__(self, task_callback: Callable, task_context: Any, result_queue: multiprocessing.Queue):
        super().__init__(command_prefix="?")

        self.task_callback = task_callback
        self.task_context = task_context
        self.result_queue = result_queue

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

        if self.task_callback:
            task_result = await self.task_callback(self)
            if self.result_queue:
                self.result_queue.put(task_result)

        self.loop.create_task(self.shutdown())

    async def shutdown(self):
        await asyncio.sleep(1) 
        os._exit(0)


# ---------------------------- tasks ------------------------------

async def get_channel_name_task(bot: InfoResolver) -> str | None:
    channel_id = bot.task_context 

    if not channel_id:
        return None

    try:
        channel = await bot.fetch_channel(channel_id)
        return getattr(channel, "name", None)
    except Exception:
        return None

async def get_guild_name_task(bot: InfoResolver) -> str | None:
    guild_id = bot.task_context 

    if not guild_id:
        return None

    try:
        guild = await bot.fetch_guild(guild_id)
        return guild.name
    except Exception:
        return None

async def get_guild_name_and_channel_name_task(bot: InfoResolver) -> tuple[str | None, str | None]:
    if not bot.task_context:
        return (None, None)

    guild_id = bot.task_context[0]
    channel_id = bot.task_context[1]

    guild_name = None
    channel_name = None

    try:
        guild = await bot.fetch_guild(guild_id)
        guild_name = guild.name
    except Exception:
        pass

    try:
        channel = await bot.fetch_channel(channel_id)
        channel_name = getattr(channel, "name", None)
    except Exception:
        pass

    return (guild_name, channel_name)

async def get_accound_id_and_name_task(bot: InfoResolver) -> tuple[int | None, str | None]:
    if bot.user is not None:
        return (bot.user.id, bot.user.name)
    return (None, None)

# ----------------------- runners ---------------------------

def run_get_channel_name(token: str, channel_id: int, queue: multiprocessing.Queue):
    client = InfoResolver(
            task_callback=get_channel_name_task,
            task_context=channel_id,
            result_queue=queue
        )

    client.run(token)

def run_get_guild_name(token: str, guild_id: int, queue: multiprocessing.Queue):
    client = InfoResolver(
            task_callback=get_guild_name_task,
            task_context=guild_id,
            result_queue=queue
        )

    client.run(token)

def run_get_guild_name_and_channel_name(token: str, guild_id: int, channel_id: int, queue: multiprocessing.Queue):
    client = InfoResolver(
            task_callback=get_guild_name_and_channel_name_task,
            task_context=(guild_id, channel_id),
            result_queue=queue
        )

    client.run(token)

def run_get_accound_id_and_name(token: str, queue: multiprocessing.Queue):
    client = InfoResolver(
            task_callback=get_accound_id_and_name_task,
            task_context=None,
            result_queue=queue
        )

    client.run(token)