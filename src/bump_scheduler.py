import logging
import sys
import time
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Prompt

from src import data_manager
from src.data_manager import DataManager
from src.console import console

logger = logging.getLogger(__name__)


class BumpScheduler():
    def __init__(self, data_manager: DataManager) -> None:
        self.bump_count = 0
        self.data_manager = data_manager
        logger.info("Starting...")

    def run(self):
        while True:
            try:
                self._bumping()
            except KeyboardInterrupt:
                sys.exit(0)

    def _bumping(self):
        if not self.data_manager.selfbots or not self.data_manager.servers:
            logger.warning("No selfbots or servers configured.")
            time.sleep(5)
            self.data_manager = DataManager()
            logger.info("Retrying...")
            return

        for server in self.data_manager.servers:
            guild_id = int(server.guild_id)

            if server.is_bumpable():
                logger.info(f"Server {server.guild_name} is bumpable. Searching for available selfbot...")

                for selfbot in self.data_manager.selfbots.values():

                    if self.data_manager.is_selfbot_able_to_bump(selfbot.id):
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

        # check state while waiting fo be more reactive to ctrl-c
        # we do not have any state idk if it's reactive like that
        for _ in range(60):
            time.sleep(1)


