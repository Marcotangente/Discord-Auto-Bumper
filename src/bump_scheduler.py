from enum import IntEnum
import logging
import sys
import time
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Prompt

from src.json_manager import DataManager
from src.console import console

logger = logging.getLogger(__name__)

class ProgramState(IntEnum):
    BUMPING = 0
    CONFIGURATING = 1
    EXIT = 2

class BumpScheduler():
    def __init__(self, data_manager: DataManager) -> None:
        self.bump_count = 0
        self.data_manager = data_manager
        self.state = ProgramState.BUMPING
        logger.info("Starting auto-bump loop...")

    def loop(self):
        while self.state != ProgramState.EXIT:
            if self.state == ProgramState.BUMPING:
                try:
                    self._bumping()
                except KeyboardInterrupt:
                    console.print("\n")
                    logger.info("Switching to configuration mode...")
                    self.state = ProgramState.CONFIGURATING
                    time.sleep(1.5)

            elif self.state == ProgramState.CONFIGURATING:
                try:
                    self._configurating()
                except KeyboardInterrupt:
                    console.print("\n")
                    self.state = ProgramState.EXIT

        self._exit()

    def _bumping(self):
        if not self.data_manager.selfbots or not self.data_manager.servers:
            logger.warning("No selfbots or servers configured. Entering configuration mode.")
            self.state = ProgramState.CONFIGURATING
            time.sleep(3.33)
            return

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
        for _ in range(10):
            if self.state != ProgramState.BUMPING:
                break
            time.sleep(1)

    def _configurating(self):
        console.clear()

        menu_table = Table(show_header=False, box=None, padding=(0, 2))
        menu_table.add_column("ID", style="bold cyan", justify="right")
        menu_table.add_column("Description", style="white")
        menu_table.add_row("1.", "Resume Auto Bumper Loop")
        menu_table.add_row("2.", "Display selfbots")
        menu_table.add_row("3.", "Register new selfbot")
        menu_table.add_row("4.", "Remove selfbot")
        menu_table.add_row("5.", "Display servers")
        menu_table.add_row("6.", "Register new server")
        menu_table.add_row("7.", "Remove server")
        menu_table.add_row("8.", "Reorder servers")
        menu_table.add_row(None, None)
        menu_table.add_row("0.", "Close program")

        menu_panel = Panel(
            menu_table,
            title="[bold magenta]CONFIG MANAGER[/]",
            border_style="purple4",
            expand=False,
        )
        
        console.print("\n")
        console.print(menu_panel)

        choice = Prompt.ask(
            "Please select an option", 
            choices=["0", "1", "2", "3", "4", "5", "6", "7", "8"],
            show_choices=False
        )

        match choice:
            case "1":
                console.clear()
                logger.info("Resuming auto-bump loop...")
                self.state = ProgramState.BUMPING
            case "2":
                self.data_manager.display_selfbots()
                console.input("Press [#99aab5]Enter[/] to continue...")
            case "3":
                token = console.input("Account token: ")
                service = self.data_manager.register_and_start_selfbot_service(token)
                if service is not None:
                    service.stop()
            case "4":
                guild_id = console.input("Selfbot ID to remove: ")
                if guild_id.isdigit():
                    self.data_manager.remove_selfbot(int(guild_id))
                else:
                    console.print("Invalid ID.")
                time.sleep(2)
            case "5":
                self.data_manager.display_servers()
                console.input("Press [#99aab5]Enter[/] to continue...")
            case "6":
                guild_id = console.input("Server ID: ")
                channel_id = console.input("Channel ID: ")
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
                    console.print("Invalid inputs.")
                time.sleep(2)
            case "7":
                guild_id = console.input("Server ID to remove: ")
                if guild_id.isdigit():
                    self.data_manager.remove_server(int(guild_id))
                else:
                    console.print("Invalid ID.")
                time.sleep(2)

            case "8":
                self._reorder_servers()

            case "0":
                self.state = ProgramState.EXIT
            case _:
                console.print("Invalid option.")

    def _reorder_servers(self):
        save = False
        temporary_server_list = self.data_manager.servers.copy()
        while True:
            console.clear()
            self._display_reordering_servers(temporary_server_list)
            user_input = Prompt.ask(
                "Enter [bold cyan]index target[/] to move, [bold green]s[/]ave, or [bold red]q[/]uit",
                default="q",
                show_default=False
            )
            if user_input == "s" or user_input == "save":
                save = True
                break

            if user_input == "q" or user_input == "quit":
                break

            splitted_input = user_input.split()
            if len(splitted_input) != 2:
                console.print("[red]Error:[/] Please enter exactly two numbers separated by a space.")
                time.sleep(1.5)
                continue
            try:
                current_index = int(splitted_input[0])
                target_index = int(splitted_input[1])

                # actual indices
                current_index -= 1
                target_index -= 1

                if current_index < 0 or current_index >= len(temporary_server_list):
                    console.print("[red]Error:[/] Please enter a valid index")
                    time.sleep(1.5)
                    continue
                target_index = max(0, target_index)
                target_index = min(target_index, len(temporary_server_list) - 1)

                server = temporary_server_list.pop(current_index)
                temporary_server_list.insert(target_index, server)

            except ValueError:
                console.print("[red]Error:[/] Please enter exactly two numbers separated by a space.")
                time.sleep(1.5)
                    
        if save:
            self.data_manager.change_order_of_servers(temporary_server_list)
            time.sleep(3)
        else:
            console.print("[yellow]No changes were made.[/]")
            time.sleep(1.5)


    def _display_reordering_servers(self, server_list: list):
        console.print("\n")
        if not server_list:
            console.print("[red]No servers.[/red]")
            return

        server_table = Table(title=f"Servers order", box=box.ROUNDED)

        server_table.add_column("Index", style="purple")
        server_table.add_column("Server Name", style="blue")

        for index, server in enumerate(server_list, start=1):

            server_table.add_row(
                str(index),
                f"{server['GuildName']}",
            )

        console.print(server_table)


    def _exit(self):
        console.print(f"Goodbye ! {self.bump_count} bump sent this session.")
        time.sleep(1.75)
        sys.exit(0)