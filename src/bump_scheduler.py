from enum import IntEnum
import time
from src.autobump_selfbot_service import AutoBumpSelfbotService
from src.json_manager import DataManager

class ProgramState(IntEnum):
    BUMPING = 0
    CONFIGURATING = 1
    EXIT = 2


class BumpScheduler():
    def __init__(self, data_manager: DataManager) -> None:
        self.data_manager = data_manager
        self.state = ProgramState.BUMPING

    def loop(self):
        while self.state != ProgramState.EXIT:
            if self.state == ProgramState.BUMPING:
                self.bumping()
            elif self.state == ProgramState.CONFIGURATING:
                self.configurating()
        self.exit()

    def bumping(self):
        for server in self.data_manager.servers:
            if self.data_manager.is_server_bumpable(int(server["GuildId"])):
                for selfbot_id in self.data_manager.selfbots.keys():
                    if self.data_manager.is_selfbot_able_to_bump(int(selfbot_id)):
                        selfbot_service = self.data_manager.update_and_start_selfbot_service(int(selfbot_id))
                        if selfbot_service is not None:
                            self.data_manager.update_server(int(server["GuildId"]), selfbot_service)
                            selfbot_service.bump_server(int(server["ChannelId"]))
                            result = selfbot_service.wait_for_bump_result(5)
                            if result:
                                self.data_manager.set_server_cooldown(int(server["GuildId"]), result.next_bump_delay_minutes)
                                if result.success:
                                    self.data_manager.set_selfbot_cooldown(int(selfbot_id), 30)
                                    break # no need to use another selfbot

                    time.sleep(1)


        time.sleep(10)

    def configurating(self):
        input("jsp")

    def exit(self):
        print("exit (pls do CTRL C)")