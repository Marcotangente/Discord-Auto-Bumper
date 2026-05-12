import logging
import sys
import time
import os
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Prompt
import random

from src.data_manager import DataManager
from src.console import console

logger = logging.getLogger(__name__)

MIN_WAIT = int(os.getenv("MIN_WAIT_TIME", 30))
MAX_WAIT = int(os.getenv("MAX_WAIT_TIME", 120))

class BumpScheduler():
    def __init__(self, data_manager: DataManager) -> None:
        self.bump_count = 0
        self.data_manager = data_manager
        logger.info("Starting...")

    def run(self):
        while True:
            try:
                self.data_manager = DataManager() # reload data in case of config change
                # maybe it's not optimal
                self._bumping()
            except KeyboardInterrupt:
                sys.exit(0)

    def _bumping(self):
        if not self.data_manager.selfbots or not self.data_manager.servers:
            logger.warning("No selfbots or servers configured.")
            time.sleep(5)
            logger.info("Retrying...")
            return

        for server in self.data_manager.servers:
            guild_id = int(server.guild_id)

            if server.is_bumpable():
                logger.info(f"Server {server.guild_name} is bumpable. Searching for available selfbot...")

                selfbots = [selfbot for selfbot in self.data_manager.selfbots.values() if selfbot.is_able_to_bump()]
                random.shuffle(selfbots)

                if selfbots:

                    for selfbot in selfbots:

                        logger.info(f"Trying to bump with selfbot {selfbot.name}...")
                        selfbot_service = self.data_manager.update_and_start_selfbot_service(selfbot.id)

                        if selfbot_service is not None:
                            self.data_manager.update_server(guild_id, selfbot_service)

                            logger.info(f"Sending bump command to channel {server.channel_name}...")
                            selfbot_service.bump_server(server.channel_id)

                            result = selfbot_service.wait_for_bump_result(5)
                            selfbot_service.stop()

                            if result:
                                if result.success:
                                    logger.info(f"Server bumped! Next bump in {result.next_bump_delay_minutes} min.")
                                    self.data_manager.set_selfbot_cooldown(selfbot.id, 30)
                                    self.bump_count += 1
                                else:
                                    logger.info(f"Bump failed. Cooldown set to {result.next_bump_delay_minutes} min.")

                                self.data_manager.set_server_cooldown(guild_id, result.next_bump_delay_minutes)

                                if result.success:
                                    break # move to next server
                            else:
                                logger.warning("No result received from Discord.")

                    time.sleep(1)

                else:
                    logger.info(f"The server {server.guild_name} is bumpable but there isn't any available selfbot... consider registering another selfbot.")

        cooldown = self.data_manager.compute_global_cooldown()
        random_cooldown = random.uniform(MIN_WAIT, MAX_WAIT)
        cooldown += random_cooldown
        hours, minutes = divmod(cooldown/60, 60)
        logger.info(f"Sleeping for {int(hours)} hours and {int(minutes)} minutes...")

        time.sleep(cooldown)


