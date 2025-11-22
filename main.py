import os
from dotenv import load_dotenv
import multiprocessing

from src.bumper_selfbot import run_bump_task
import src.json_manager as json_manager

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = 1396626329129975849

# bot_process = multiprocessing.Process(target=run_bump_task, args=(DISCORD_TOKEN, CHANNEL_ID))
# bot_process.start()
# bot_process.join()

json_manager.register_bot("853579408383803444", DISCORD_TOKEN, "moii")
json_manager.register_channel(str(CHANNEL_ID), "pas de nom")
