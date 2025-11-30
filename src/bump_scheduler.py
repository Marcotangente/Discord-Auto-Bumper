from enum import IntEnum
import logging
import sys
import time
from datetime import datetime

import discord
from src.autobump_selfbot_service import AutoBumpSelfbotService
from src.json_manager import DataManager

logger = logging.getLogger(__name__)

class ProgramState(IntEnum):
    BUMPING = 0
    CONFIGURATING = 1
    EXIT = 2

class BumpScheduler():
    def __init__(self, data_manager: DataManager) -> None:
        self.data_manager = data_manager
        if not self.data_manager.selfbots or not self.data_manager.servers:
            logger.warning("No selfbots or servers configured. Entering configuration mode.")
            self.state = ProgramState.CONFIGURATING
        else:
            self.state = ProgramState.BUMPING
            logger.info("Scheduler initialized. Starting loop...")

    def loop(self):
        while self.state != ProgramState.EXIT:
            if self.state == ProgramState.BUMPING:
                try:
                    self.bumping()
                except KeyboardInterrupt:
                    print("\n")
                    logger.info("Switching to configuration mode...")
                    self.state = ProgramState.CONFIGURATING

            elif self.state == ProgramState.CONFIGURATING:
                try:
                    self.configurating()
                except KeyboardInterrupt:
                    print("\n")
                    self.state = ProgramState.EXIT

        self.exit()

    def bumping(self):
        for server in self.data_manager.servers:
            guild_id = int(server["GuildId"])
            
            if self.data_manager.is_server_bumpable(guild_id):
                logger.info(f"Server {guild_id} is bumpable. Searching for available selfbot...")
                
                for selfbot_id in self.data_manager.selfbots.keys():
                    sb_id = int(selfbot_id)
                    
                    if self.data_manager.is_selfbot_able_to_bump(sb_id):
                        logger.info(f"Trying to bump with selfbot {self.data_manager.selfbots[selfbot_id]["Name"]}...")

                        selfbot_service = self.data_manager.update_and_start_selfbot_service(sb_id)

                        if selfbot_service is not None:
                            self.data_manager.update_server(guild_id, selfbot_service)

                            logger.info(f"Sending bump command to channel {server['ChannelId']}...")
                            selfbot_service.bump_server(int(server["ChannelId"]))

                            result = selfbot_service.wait_for_bump_result(5)
                            selfbot_service.stop()

                            if result:
                                if result.success:
                                    logger.info(f"Server bumped! Next bump in {result.next_bump_delay_minutes} min.")
                                    self.data_manager.set_selfbot_cooldown(sb_id, 30)
                                else:
                                    logger.info(f"Bump failed. Cooldown set to {result.next_bump_delay_minutes} min.")

                                self.data_manager.set_server_cooldown(guild_id, result.next_bump_delay_minutes)

                                if result.success:
                                    break # move to next server
                            else:
                                logger.error("No result received from Discord.")

                    time.sleep(1)

        # check state while waiting fo be more reactive to ctrl-c
        for _ in range(10):
            if self.state != ProgramState.BUMPING:
                break
            time.sleep(1)

    def configurating(self):
        print("\n" + "="*10 + " CONFIG MANAGER " + "="*10)
        print("1. Auto Bumper Loop")
        print("2. Display selfbots")
        print("3. Register new selfbot")
        print("4. Remove selfbot")
        print("5. Display servers")
        print("6. Register new server")
        print("7. Remove server")
        print("0. Close program")
        print("="*36)
        
        try:
            choice = input("Select an option: ").strip()
        except EOFError:
            return # handle abrupt closing

        if choice == "1":
            logger.info("Resuming auto-bump loop...")
            self.state = ProgramState.BUMPING
        elif choice == "2":
            self.data_manager.display_selfbots()
            input("Press Enter to continue...")
        elif choice == "3":
            token = input("Account token: ")
            service = self.data_manager.register_and_start_selfbot_service(token)
            if service is not None:
                service.stop()
        elif choice == "4":
            bot_id = input("Selfbot ID to remove: ")
            if bot_id.isdigit():
                self.data_manager.remove_selfbot(int(bot_id))
                print(f"Selfbot {bot_id} removed.")
            else:
                print("Invalid ID.")
        elif choice == "5":
            self.data_manager.display_servers()
            input("Press Enter to continue...")
        elif choice == "6":
            guild_id = input("Server ID: ")
            channel_id = input("Channel ID: ")
            if guild_id.isdigit() and channel_id.isdigit():
                for selfbot_id in self.data_manager.selfbots.keys():
                    sb_id = int(selfbot_id)
                    selfbot_service = self.data_manager.update_and_start_selfbot_service(sb_id)
                    if selfbot_service is not None:
                        registered = self.data_manager.register_server(int(guild_id), int(channel_id), selfbot_service)
                        selfbot_service.stop()
                        if registered:
                            break
            else:
                print("Invalid inputs.")

        elif choice == "0":
            self.state = ProgramState.EXIT
        else:
            print("Invalid option.")

    def exit(self):
        logger.info("Shutting down services and exiting. Goodbye!")
        sys.exit(0)