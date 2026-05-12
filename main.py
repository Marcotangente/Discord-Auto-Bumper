import asyncio
import logging
import sys
import argparse
import rich.text
import rich.panel

from rich.logging import RichHandler

from src import data_manager
from src.bump_scheduler import BumpScheduler
from src.configurator import Configurator
from src.console import console
from src.data_manager import DataManager

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

def main():
    parser = argparse.ArgumentParser(description="Discord Auto Bumper")
    parser.add_argument(
        "--config",
        action="store_true"
    )
    args = parser.parse_args()

    data_manager = DataManager()

    if args.config:
        config_manager = Configurator(data_manager)
        config_manager.run()
    else:
        bmp = BumpScheduler(data_manager)
        bmp.run()

if __name__ == "__main__":
    main()
