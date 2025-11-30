import logging

import discord
from src.bump_scheduler import BumpScheduler
import src.json_manager as json_manager

discord.utils.setup_logging(level=logging.INFO)

logging.getLogger('discord').setLevel(logging.ERROR)
logging.getLogger('discord.http').setLevel(logging.ERROR)
logging.getLogger('discord.state').setLevel(logging.ERROR)
logging.getLogger('discord.client').setLevel(logging.ERROR)
logging.getLogger('discord.gateway').setLevel(logging.ERROR)


data_manager = json_manager.DataManager()
bmp = BumpScheduler(data_manager)
bmp.loop()
