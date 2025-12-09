import asyncio
import logging
import sys
from rich.logging import RichHandler

import discord
from src.bump_scheduler import BumpScheduler
from src.console import console
import src.json_manager as json_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(
            show_path=False,
            rich_tracebacks=True,
            omit_repeated_times=False,
            console=console
        )
    ]
)

logging.getLogger('discord').setLevel(logging.ERROR)
logging.getLogger('discord.http').setLevel(logging.ERROR)
logging.getLogger('discord.state').setLevel(logging.ERROR)
logging.getLogger('discord.client').setLevel(logging.ERROR)
logging.getLogger('discord.gateway').setLevel(logging.ERROR)

if sys.platform == "win32": 
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

with console.screen():
    data_manager = json_manager.DataManager()
    bmp = BumpScheduler(data_manager)
    bmp.loop()
