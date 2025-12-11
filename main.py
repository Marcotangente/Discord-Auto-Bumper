import asyncio
import logging
import sys
import time
import rich.text
import rich.panel

from rich.logging import RichHandler

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
    welcome_text = rich.text.Text()
    welcome_text.append("Welcome !\n", style="bold purple")
    welcome_text.append("Press ", style="dim")
    welcome_text.append("Ctrl+C", style="bold red reverse")
    welcome_text.append(" at any time to open the Config Manager.", style="dim")
    banner = rich.panel.Panel(
        welcome_text,
        title="[bold blue]Discord Auto Bumper[/bold blue]",
        border_style="purple",
        padding=(1, 2)
    )
    console.print(banner)
    time.sleep(0.4)
    data_manager = json_manager.DataManager()
    bmp = BumpScheduler(data_manager)
    bmp.loop()
