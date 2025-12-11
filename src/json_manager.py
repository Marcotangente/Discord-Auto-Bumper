import json
import logging
import time
from pathlib import Path
from rich.table import Table
from rich import box
from src.autobump_selfbot_service import AutoBumpSelfbotService
from src.console import console

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
        
        self.selfbots: dict[str, dict[str, str | int]] = {}
        self.servers: list[dict[str, int | str]] = []
        
        self._ensure_data_directory()
        self._load_selfbots_data()
        self._load_servers_data()

    def _ensure_data_directory(self):
        """Create the data directory if it doesn't exist."""
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def _load_selfbots_data(self):
        if self._selfbots_path.exists():
            with open(self._selfbots_path, "r", encoding='utf-8') as f:
                try:
                    self.selfbots = json.load(f)
                except json.JSONDecodeError:
                    console.print(f"Error loading file: {self._selfbots_path}")

    def _load_servers_data(self):
        if self._servers_path.exists():
            with open(self._servers_path, "r", encoding='utf-8') as f:
                try:
                    self.servers = json.load(f)
                except json.JSONDecodeError:
                    console.print(f"Error loading file: {self._servers_path}")

    def _save_selfbots(self):
        with open(self._selfbots_path, "w", encoding='utf-8') as file:
            json.dump(self.selfbots, file, indent=4)

    def _save_servers(self):
        with open(self._servers_path, "w", encoding='utf-8') as file:
            json.dump(self.servers, file, indent=4)

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
        id_str = str(id)
        name = res[1]

        if id_str in self.selfbots:
            console.print(f"Selfbot '{name}' (ID: {id}) is already registered.")
            return selfbot_service

        self.selfbots[id_str] = {
            "Token": token,
            "Name": name,
            "NextBumpTimestamp": -1
        }
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

        id_str = str(id)
        selfbot = self.selfbots.get(id_str)
        if selfbot is None:
            console.print(f"Selfbot ID {id} is not registered.")
            return None

        selfbot_service = AutoBumpSelfbotService(selfbot["Token"]) # type: ignore

        res = selfbot_service.get_account_id_and_name()
        if res is None:
            console.print(f"Error updating selfbot ID {id}: Could not retrieve account info.")
            selfbot_service.stop()
            return None

        name = res[1]

        if selfbot["Name"] != name:
            console.print(f"Updated selfbot name (ID: {id}): '{self.selfbots[id_str]["Name"]}' -> '{name}'.")
            selfbot["Name"] = name
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

        id_str = str(selfbot_id)
        if id_str in self.selfbots:
            removed_bot = self.selfbots.pop(id_str)
            self._save_selfbots()
            console.print(f"Selfbot '{removed_bot['Name']}' (ID: {selfbot_id}) removed successfully.")
        else:
            console.print(f"Selfbot ID {selfbot_id} not found.")

    def is_selfbot_able_to_bump(self, id: int) -> bool:
        """Check if the personal cooldown of the selfbot has expired."""

        selfbot = self.selfbots.get(str(id))
        if selfbot is None or not isinstance(selfbot["NextBumpTimestamp"], int) :
            return False
        return selfbot["NextBumpTimestamp"] <= time.time()

    def set_selfbot_cooldown(self, id: int, cooldown: int):
        """Set the personal cooldown for a selfbot."""
        selfbot = self.selfbots.get(str(id))
        if selfbot is None:
            console.print(f"Selfbot ID {id} is not registered.")
            return

        if isinstance(selfbot["NextBumpTimestamp"], int):
            selfbot["NextBumpTimestamp"] = round(time.time()) + cooldown * 60
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


        existing_server = next((server for server in self.servers if server["GuildId"] == guild_id), None)
        if existing_server is not None:
            console.print(f"Server '{guild_name}' is already registered.")
            return False

        if channel_name is not None:
            new_server = {
                "GuildId": guild_id,
                "GuildName": guild_name,
                "ChannelId": channel_id,
                "ChannelName": channel_name,
                "NextBumpTimestamp" : -1
            }
            self.servers.append(new_server)
            console.print(f"Server '{guild_name}' (ID: {guild_id}) saved with channel '{channel_name}' (ID: {channel_id}).")
        else:
            new_server = {
                "GuildId": guild_id,
                "GuildName": guild_name,
                "ChannelId": -1,
                "ChannelName": "NO CHANNEL",
                "NextBumpTimestamp" : -1
            }
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

        existing_server = next((server for server in self.servers if server["GuildId"] == guild_id), None)
        if existing_server is None:
            console.print(f"Server ID {guild_id} is not registered.")
            return

        if existing_server["ChannelId"] == channel_id:
            console.print(f"Channel for server '{existing_server['GuildName']}' is unchanged.")
            return

        channel_name = selfbot_service.get_channel_name(channel_id)

        if channel_name is None:
            console.print(f"Channel ID {channel_id} not found.")
            return

        console.print(f"Updated channel for server '{existing_server['GuildName']}': '{existing_server['ChannelName']}' -> '{channel_name}'.")
        existing_server["ChannelId"] = channel_id
        existing_server["ChannelName"] = channel_name

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
        existing_server = next((server for server in self.servers if server["GuildId"] == guild_id), None)
        if existing_server is None:
            console.print(f"Server '{guild_name}' is not registered.")
            return

        channel_id: int = existing_server["ChannelId"] # type: ignore
        channel_name = selfbot_service.get_channel_name(channel_id)
        if channel_name is None:
            console.print(f"Channel ID {channel_id} not found (Server: '{guild_name}').")

        if existing_server["GuildName"] != guild_name and guild_name is not None:
            console.print(f"Updated server name (ID: {guild_id}): '{existing_server['GuildName']}' -> '{guild_name}'.")
            existing_server["GuildName"] = guild_name
            should_save = True

        if existing_server["ChannelName"] != channel_name and channel_name is not None:
            console.print(f"Updated channel name for '{guild_name}': '{existing_server['ChannelName']}' -> '{channel_name}'.")
            existing_server["ChannelName"] = channel_name
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
        self.servers[:] = [server for server in self.servers if server["GuildId"] != guild_id]
        removed_count = initial_count - len(self.servers)
        if removed_count > 0:
            self._save_servers()

            console.print(f"Server ID {guild_id} removed successfully.")
        else:
            console.print(f"Server ID {guild_id} not found.")

    def is_server_bumpable(self, id: int) -> bool:
        """Check if the cooldown of the server has expired."""

        server = next((server for server in self.servers if server["GuildId"] == id), None)
        if server is None or not isinstance(server["NextBumpTimestamp"], int) :
            return False
        return server["NextBumpTimestamp"] <= time.time()

    def set_server_cooldown(self, id: int, cooldown: int):
        """Set the personal cooldown for a selfbot."""

        server = next((server for server in self.servers if server["GuildId"] == id), None)
        if server is None:
            console.print(f"Server ID {id} is not registered.")
            return

        if isinstance(server["NextBumpTimestamp"], int):
            server["NextBumpTimestamp"] = round(time.time()) + cooldown * 60
            self._save_servers()

    def change_order_of_servers(self, new_server_list: list):
        required_keys = {"GuildId", "GuildName", "ChannelId", "ChannelName", "NextBumpTimestamp"}
        is_valid = all(server.keys() == required_keys for server in new_server_list)
        if is_valid:
            if new_server_list != self.servers:
                self.servers = new_server_list
                self._save_servers()
                console.print("[green]Server order changed.")
            else:
                console.print("[yellow]New order is the same as before, no changes.[/]")
        else:
            console.print(f"[red]Error:[/] new server list do not contains the required keys ({required_keys})")

    def display_selfbots(self):
        console.print("\n")
        if not self.selfbots:
            console.print("[red]No bots found.[/red]")
            return

        selfbot_table = Table(title="Registered Selfbots", box=box.ROUNDED)

        selfbot_table.add_column("ID", style="cyan", no_wrap=True)
        selfbot_table.add_column("Name", style="magenta")
        selfbot_table.add_column("Status", justify="right")

        for bot_id, bot_data in self.selfbots.items():
            now = time.time()
            minutes_remaining = (bot_data["NextBumpTimestamp"] - now) / 60 # type: ignore
            
            if minutes_remaining <= 0:
                time_display = "[bold green]Ready to bump![/]"
            else:
                time_display = f"[yellow]Ready in {round(minutes_remaining)} min[/]"

            selfbot_table.add_row(
                str(bot_id),
                str(bot_data['Name']),
                time_display
            )

        console.print(selfbot_table)

    def display_servers(self, show_index: bool = False):
        console.print("\n")
        if not self.servers:
            console.print("[red]No servers found.[/red]")
            return

        server_table = Table(title=f"Registered Servers ({len(self.servers)})", box=box.ROUNDED)

        if show_index:
            server_table.add_column("Index", style="purple")
        server_table.add_column("Server Name", style="blue")
        if not show_index:
            server_table.add_column("Target Channel", style="cyan")
            server_table.add_column("Status", justify="right")

        for index, server in enumerate(self.servers, start=1):
            now = time.time()
            minutes_remaining = (server["NextBumpTimestamp"] - now) / 60 # type: ignore

            if minutes_remaining <= 0:
                status_display = "[bold green]Ready to bump[/]"
            else:
                status_display = f"[yellow]{round(minutes_remaining)} min until bump[/]"

            if show_index:
                server_table.add_row(
                    str(index),
                    f"{server['GuildName']}",
                )
            else:
                server_table.add_row(
                    f"{server['GuildName']}",
                    f"{server['ChannelName']}",
                    status_display
                )

        console.print(server_table)