from dataclasses import dataclass, asdict
import json
import logging
import time
from pathlib import Path
from rich.table import Table
from rich import box
from src.autobump_selfbot_service import AutoBumpSelfbotService
from src.console import console
import math

@dataclass
class Selfbot:
    token: str
    id: int
    name: str
    next_bump_timestamp: int = -1

    def is_able_to_bump(self) -> bool:
        return self.next_bump_timestamp <= time.time()

@dataclass
class Server:
    guild_id: int
    guild_name: str
    channel_id: int
    channel_name: str
    next_bump_timestamp: int = -1

    def is_bumpable(self) -> bool:
        return self.next_bump_timestamp <= time.time()

class DataManager():
    """
    Manages all the data.

    Attributes
    ----------
    selfbots : dict[str, dict[str, str | int]]
        Contains selfbot data, keyed by account ID (str). Each value is a dict 
        containing the keys "Token", "Name" (str) and "NextBumpTimestamp" (int).
    servers : list[dict[str, int | str]]
        List of server/channel configurations. Each dictionary contains the keys 
        "GuildId" (int), "GuildName" (str), "ChannelId" (int), "ChannelName" (str) 
        and "NextBumpTimestamp" (int).
    """

    def __init__(self, data_dir: str = "data"):
        """Load the json data."""
        self._root = Path(__file__).parent.parent
        self._data_dir = self._root / data_dir
        self._selfbots_path = self._data_dir / "selfbots.json"
        self._servers_path = self._data_dir / "servers.json"

        self._ensure_data_directory()

        self.selfbots: dict[int, Selfbot] = self._load_selfbots()
        self.servers : list[Server] = self._load_servers()


    def _ensure_data_directory(self):
        """Create the data directory if it doesn't exist."""
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def _load_selfbots(self) -> dict[int, Selfbot]:
        if self._selfbots_path.exists():
            with open(self._selfbots_path, "r", encoding='utf-8') as f:
                try:
                    raw_json = json.load(f)
                    return {
                        int(id): Selfbot(
                            token=data["Token"],
                            id=int(id),
                            name=data["Name"],
                            next_bump_timestamp=data["NextBumpTimestamp"]
                        ) for id, data in raw_json.items()
                    }
                except json.JSONDecodeError:
                    console.print(f"Error loading file: {self._selfbots_path}")

        return {}

    def _load_servers(self) -> list[Server]:
        if self._servers_path.exists():
            with open(self._servers_path, "r", encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    return [Server(**item) for item in data]
                except json.JSONDecodeError:
                    console.print(f"Error loading file: {self._servers_path}")

        return []

    def _save_selfbots(self):
        with open(self._selfbots_path, "w", encoding='utf-8') as file:
            data= {
                id: {
                    "Token": bot.token,
                    "Name": bot.name,
                    "NextBumpTimestamp": bot.next_bump_timestamp
                } for id, bot in self.selfbots.items()
            }
            json.dump(data, file, indent=4)

    def _save_servers(self):
        with open(self._servers_path, "w", encoding='utf-8') as file:
            data = [asdict(server) for server in self.servers]
            json.dump(data, file, indent=4)

    def register_and_start_selfbot_service(self, token: str) -> AutoBumpSelfbotService | None:
        """
        Register a new selfbot and start the service.

        Parameters
        ----------
        token : str
            The authentication token for the selfbot.

        Returns
        -------
        AutoBumpSelfbotService or None
            The service created from the token, or None if an error occured.
        """

        selfbot_service = AutoBumpSelfbotService(token)
        res = selfbot_service.get_account_id_and_name()
        if res is None:
            console.print("Failed to register selfbot: Invalid token or connection error.")
            selfbot_service.stop()
            return None

        id = res[0]
        name = res[1]

        if id in self.selfbots:
            console.print(f"Selfbot '{name}' (ID: {id}) is already registered.")
            return selfbot_service


        self.selfbots[id] = Selfbot(token, id, name)
        console.print(f"Selfbot '{name}' (ID: {id}) saved successfully.")

        self._save_selfbots()

        return selfbot_service

    def update_and_start_selfbot_service(self, id: int) -> AutoBumpSelfbotService | None:
        """
        Update the selfbot name and start it.
        
        Parameters
        -------
        id : int
            The id of the selfbot user account.

        Returns
        -------
        AutoBumpSelfbotService
            The service created from the id.
        None
            If an error occured.
        """

        selfbot = self.selfbots.get(id)
        if selfbot is None:
            console.print(f"Selfbot ID {id} is not registered.")
            return None

        selfbot_service = AutoBumpSelfbotService(selfbot.token)

        res = selfbot_service.get_account_id_and_name()
        if res is None:
            console.print(f"Error updating selfbot ID {id}: Could not retrieve account info.")
            selfbot_service.stop()
            return None

        name = res[1]

        if selfbot.name != name:
            console.print(f"Updated selfbot name (ID: {id}): '{selfbot.name}' -> '{name}'.")
            selfbot.name = name
            self._save_selfbots()

        return selfbot_service

    def remove_selfbot(self, selfbot_id: int):
        """
        Remove the selfbot if found.
        
        Parameters
        -------
        selfbot_id : int
            The id of the selfbot user account.
        """

        if selfbot_id in self.selfbots:
            removed_bot = self.selfbots.pop(selfbot_id)
            self._save_selfbots()
            console.print(f"Selfbot '{removed_bot.name}' (ID: {selfbot_id}) removed successfully.")
        else:
            console.print(f"Selfbot ID {selfbot_id} not found.")

    def is_selfbot_able_to_bump(self, id: int) -> bool:
        """Check if the personal cooldown of the selfbot has expired."""

        selfbot = self.selfbots.get(id)
        if selfbot is None:
            return False
        return selfbot.is_able_to_bump()

    def set_selfbot_cooldown(self, id: int, cooldown: int):
        """Set the personal cooldown for a selfbot."""
        selfbot = self.selfbots.get(id)
        if selfbot is None:
            console.print(f"Selfbot ID {id} is not registered.")
            return

        selfbot.next_bump_timestamp = round(time.time()) + cooldown * 60
        self._save_selfbots()

    def register_server(self, guild_id: int, channel_id: int, selfbot_service: AutoBumpSelfbotService) -> bool:
        """
        Register a new server and the channel associated.

        Parameters
        -------
        guild_id : int
            The id of the server to register.
        channel_id : int
            The id of the channel to register with the server.
        selfbot_service : AutoBumpSelfbotService
            A selfbot service which has an access to the server and channel.

        Return
        -------
        bool
            True if success, False otherwise.
        """

        guild_name = selfbot_service.get_guild_name(guild_id)
        channel_name = selfbot_service.get_channel_name(channel_id)

        if guild_name is None:
            console.print(f"Server ID {guild_id} not found.")
            return False

        if channel_name is None:
            console.print(f"Channel ID {channel_id} not found.")


        existing_server = next((server for server in self.servers if server.guild_id == guild_id), None)
        if existing_server is not None:
            console.print(f"Server '{guild_name}' is already registered.")
            return False

        if channel_name is not None:
            new_server = Server(guild_id, guild_name, channel_id, channel_name)
            self.servers.append(new_server)
            console.print(f"Server '{guild_name}' (ID: {guild_id}) saved with channel '{channel_name}' (ID: {channel_id}).")
        else:
            new_server = Server(guild_id, guild_name, -1, "NO CHANNEL")
            self.servers.append(new_server)
            console.print(f"Server '{guild_name}' (ID: {guild_id}) saved without channel. Please update channel.")

        self._save_servers()
        return True

    def change_server_channel(self, guild_id: int, channel_id: int, selfbot_service: AutoBumpSelfbotService):
        """
        Change the channel associated with a server.
        
        Parameters
        -------
        guild_id : int
            The id of the server to change.
        channel_id : int
            The id of the new channel to register with the server.
        selfbot_service : AutoBumpSelfbotService
            A selfbot service which has an access to the server and channel.
        """

        existing_server = next((server for server in self.servers if server.guild_id == guild_id), None)
        if existing_server is None:
            console.print(f"Server ID {guild_id} is not registered.")
            return

        if existing_server.channel_id == channel_id:
            console.print(f"Channel for server '{existing_server.guild_name}' is unchanged.")
            return

        channel_name = selfbot_service.get_channel_name(channel_id)

        if channel_name is None:
            console.print(f"Channel ID {channel_id} not found.")
            return

        console.print(f"Updated channel for server '{existing_server.guild_name}': '{existing_server.channel_name}' -> '{channel_name}'.")
        existing_server.channel_id = channel_id
        existing_server.channel_name = channel_name

        self._save_servers()

    def update_server(self, guild_id: int, selfbot_service: AutoBumpSelfbotService):
        """
        Update the name of the server and its associated channel.

        Parameters
        -------
        guild_id : int
            The id of the server to update.
        selfbot_service : AutoBumpSelfbotService
            A selfbot service which has an access to the server.
        """

        guild_name = selfbot_service.get_guild_name(guild_id)

        if guild_name is None:
            console.print(f"Server ID {guild_id} not found.")
            return

        should_save = False
        existing_server = next((server for server in self.servers if server.guild_id == guild_id), None)
        if existing_server is None:
            console.print(f"Server '{guild_name}' is not registered.")
            return

        channel_id: int = existing_server.channel_id
        channel_name = selfbot_service.get_channel_name(channel_id)
        if channel_name is None:
            console.print(f"Channel ID {channel_id} not found (Server: '{guild_name}').")

        if existing_server.guild_name != guild_name and guild_name is not None:
            console.print(f"Updated server name (ID: {guild_id}): '{existing_server.guild_name}' -> '{guild_name}'.")
            existing_server.guild_name = guild_name
            should_save = True

        if existing_server.channel_name != channel_name and channel_name is not None:
            console.print(f"Updated channel name for '{guild_name}': '{existing_server.channel_name}' -> '{channel_name}'.")
            existing_server.channel_name = channel_name
            should_save = True

        if should_save:
            self._save_servers()

    def remove_server(self, guild_id: int):
        """
        Remove the server if found.

        Parameters
        -------
        guild_id : int
            The id of the server.
        """
        initial_count = len(self.servers)
        self.servers[:] = [server for server in self.servers if server.guild_id != guild_id]
        removed_count = initial_count - len(self.servers)
        if removed_count > 0:
            self._save_servers()

            console.print(f"Server ID {guild_id} removed successfully.")
        else:
            console.print(f"Server ID {guild_id} not found.")

    def set_server_cooldown(self, id: int, cooldown: int):
        """Set the personal cooldown for a selfbot."""

        server = next((server for server in self.servers if server.guild_id == id), None)
        if server is None:
            console.print(f"Server ID {id} is not registered.")
            return

        server.next_bump_timestamp = round(time.time()) + cooldown * 60
        self._save_servers()

    def change_order_of_servers(self, new_server_list: list[Server]):
        if new_server_list != self.servers:
            self.servers = new_server_list
            self._save_servers()
            console.print("[green]Server order changed.")
        else:
            console.print("[yellow]New order is the same as before, no changes.[/]")

    def display_selfbots(self):
        console.print("\n")
        if not self.selfbots:
            console.print("[red]No bots found.[/red]")
            return

        selfbot_table = Table(title="Registered Selfbots", box=box.ROUNDED)

        selfbot_table.add_column("ID", style="cyan", no_wrap=True)
        selfbot_table.add_column("Name", style="magenta")
        selfbot_table.add_column("Status", justify="right")

        for bot_id, bot in self.selfbots.items():
            now = time.time()
            minutes_remaining = (bot.next_bump_timestamp - now) / 60

            if minutes_remaining <= 0:
                time_display = "[bold green]Ready to bump![/]"
            else:
                time_display = f"[yellow]Ready in {round(minutes_remaining)} min[/]"

            selfbot_table.add_row(
                str(bot_id),
                str(bot.name),
                time_display
            )

        console.print(selfbot_table)

    def display_servers(self):
        console.print("\n")
        if not self.servers:
            console.print("[red]No servers found.[/red]")
            return

        server_table = Table(title=f"Registered Servers ({len(self.servers)})", box=box.ROUNDED)

        server_table.add_column("ID", style="cyan", no_wrap=True)
        server_table.add_column("Server Name", style="blue")
        server_table.add_column("Target Channel", style="cyan")
        server_table.add_column("Status", justify="right")

        for server in self.servers:
            now = time.time()
            minutes_remaining = (server.next_bump_timestamp - now) / 60

            if minutes_remaining <= 0:
                status_display = "[bold green]Ready to bump[/]"
            else:
                status_display = f"[yellow]{round(minutes_remaining)} min until bump[/]"

            server_table.add_row(
                f"{server.guild_id}",
                f"{server.guild_name}",
                f"{server.channel_name}",
                status_display
            )

        console.print(server_table)

    def compute_global_cooldown(self) -> int:
        if not self.servers:
            return 60

        now = time.time()
        minimum_server_cooldown = min(self.servers, key=lambda server: server.next_bump_timestamp - now).next_bump_timestamp - now
        minimum_selfbot_cooldown = min(self.selfbots.values(), key=lambda selfbot: selfbot.next_bump_timestamp - now).next_bump_timestamp - now

        return math.ceil(max(minimum_server_cooldown, minimum_selfbot_cooldown, 0))
