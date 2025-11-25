import json
import os

from src.autobump_selfbot_service import AutoBumpSelfbotService

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DATA_SELFBOTS_RELATIVE = "data/selfbots.json"
DATA_SERVERS_RELATIVE = "data/servers.json"

DATA_SELFBOTS = os.path.join(PROJECT_ROOT, DATA_SELFBOTS_RELATIVE)
DATA_SERVERS = os.path.join(PROJECT_ROOT, DATA_SERVERS_RELATIVE)

def load_selfbots_data() -> dict[str, dict[str, str]]:
    if os.path.exists(DATA_SELFBOTS):
        with open(DATA_SELFBOTS, "r", encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Error while loading {DATA_SELFBOTS}")
                return {}
    return {}

def load_servers_data() -> list[dict[str, int | str]]:
    if os.path.exists(DATA_SERVERS):
        with open(DATA_SERVERS, "r", encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Error while loading {DATA_SERVERS}")
                return []
    return []

def register_and_start_selfbot(token: str) -> AutoBumpSelfbotService | None:
    selfbot_service = AutoBumpSelfbotService(token)
    res = selfbot_service.get_accound_id_and_name()
    if res is None:
        print("Error while registering selfbot.")
        selfbot_service.stop()
        return None

    id = res[0]
    id_str = str(id)
    name = res[1]

    selfbots = load_selfbots_data()
    if id_str in selfbots:
        print(f"The selfbot {name} is already registered.")
        return selfbot_service

    selfbots[id_str] = {
        "Token": token,
        "Name": name
    }
    print(f"Selfot {name} (ID: {id}) successfully saved.")

    ensure_data_directory()
    with open(DATA_SELFBOTS, "w", encoding='utf-8') as file:
        json.dump(selfbots, file, indent=4)

    return selfbot_service

def update_and_start_selfbot(id: int) -> AutoBumpSelfbotService | None:
    id_str = str(id)
    selfbots = load_selfbots_data()
    selfbot = selfbots.get(id_str)
    if selfbot is None:
        print(f"The selfbot with id {id} is not registered.")
        return None

    selfbot_service = AutoBumpSelfbotService(selfbot["Token"])

    res = selfbot_service.get_accound_id_and_name()
    if res is None:
        print(f"Error while updating selfbot with id {id}.")
        selfbot_service.stop()
        return None

    name = res[1]

    if selfbot["Name"] != name:
        print(f"Updated the name of the selfbot with id {id} ({selfbots[id_str]["Name"]} -> {name}).")
        selfbot["Name"] = name

        ensure_data_directory()
        with open(DATA_SELFBOTS, "w", encoding='utf-8') as file:
            json.dump(selfbots, file, indent=4)

    return selfbot_service

def register_server(guild_id: int, channel_id: int, selfbot_service: AutoBumpSelfbotService):

    guild_name = selfbot_service.get_guild_name(guild_id)
    channel_name = selfbot_service.get_channel_name(channel_id)

    if guild_name is None:
        print(f"Server with id {guild_id} not found.")
        return

    if channel_name is None:
        print(f"Channel with id {channel_id} not found.")

    servers = load_servers_data()

    existing_server = next((server for server in servers if server["GuildId"] == guild_id), None)
    if existing_server is not None:
        print(f"The server {guild_name} is already registered.")
        return

    if channel_name is not None:
        new_server = {
            "GuildId": guild_id,
            "GuildName": guild_name,
            "ChannelId": channel_id,
            "ChannelName": channel_name
        }
        servers.append(new_server)
        print(f"Server {guild_name} (ID: {guild_id}) successfully saved with channel {channel_name} (ID: {channel_id}).")
    else:
        new_server = {
            "GuildId": guild_id,
            "GuildName": guild_name,
            "ChannelId": -1,
            "ChannelName": "NO CHANNEL"
        }
        servers.append(new_server)
        print(f"Server {guild_name} (ID: {guild_id}) successfully saved with no channel, please update the channel.")

    ensure_data_directory()
    with open(DATA_SERVERS, "w", encoding='utf-8') as file:
        json.dump(servers, file, indent=4)

def change_server_channel(guild_id: int, channel_id: int, selfbot_service: AutoBumpSelfbotService):

    servers = load_servers_data()
    existing_server = next((server for server in servers if server["GuildId"] == guild_id), None)
    if existing_server is None:
        print(f"The server with id {guild_id} is not registered")
        return

    if existing_server["ChannelId"] == channel_id:
        print(f"The new channel for server {existing_server['GuildName']} is the same as before.")
        return

    channel_name = selfbot_service.get_channel_name(channel_id)

    if channel_name is None:
        print(f"Channel with id {channel_id} not found.")
        return

    print(f"Updated the name of the channel in server {existing_server['GuildName']} ! ({existing_server['ChannelName']} -> {channel_name})")
    existing_server["ChannelId"] = channel_id
    existing_server["ChannelName"] = channel_name

    ensure_data_directory()
    with open(DATA_SERVERS, "w", encoding='utf-8') as file:
        json.dump(servers, file, indent=4)


def update_server(guild_id: int, selfbot_service: AutoBumpSelfbotService):

    guild_name = selfbot_service.get_guild_name(guild_id)

    if guild_name is None:
        print(f"Server with id {guild_id} not found.")
        return

    should_save = False
    servers = load_servers_data()
    existing_server = next((server for server in servers if server["GuildId"] == guild_id), None)
    if existing_server is None:
        print(f"The server {guild_name} is not registered")
        return

    channel_id: int = existing_server["ChannelId"] # type: ignore
    channel_name = selfbot_service.get_channel_name(channel_id)
    if channel_name is None:
        print(f"Channel with id {channel_id} not found (Channel of server {guild_name}).")

    if existing_server["GuildName"] != guild_name and guild_name is not None:
        print(f"Updated the name of server {guild_id} ! ({existing_server['GuildName']} -> {guild_name})")
        existing_server["GuildName"] = guild_name
        should_save = True

    if existing_server["ChannelName"] != channel_name and channel_name is not None:
        print(f"Updated the name of the channel in {guild_name} ! ({existing_server['ChannelName']} -> {channel_name})")
        existing_server["ChannelName"] = channel_name
        should_save = True

    if should_save:
        ensure_data_directory()
        with open(DATA_SERVERS, "w", encoding='utf-8') as file:
            json.dump(servers, file, indent=4)


def remove_selfbot(selfbot_id: int):
    selfbots = load_selfbots_data()
    id_str = str(selfbot_id)
    if id_str in selfbots:
        removed_bot = selfbots.pop(id_str)
        ensure_data_directory()
        with open(DATA_SELFBOTS, "w", encoding='utf-8') as file:
            json.dump(selfbots, file, indent=4)
        print(f"Selfbot {removed_bot['Name']} (ID: {selfbot_id}) successfully removed.")
    else:
        print(f"Selbot with id {selfbot_id} not found.")

def remove_server(guild_id: int):
    servers = load_servers_data()
    initial_count = len(servers)
    servers[:] = [server for server in servers if server["GuildId"] != guild_id]
    removed_count = initial_count - len(servers)
    if removed_count > 0:
        ensure_data_directory()
        with open(DATA_SERVERS, "w", encoding='utf-8') as file:
            json.dump(servers, file, indent=4)
        print(f"Server with id {guild_id} successfully removed.")
    else:
        print(f"Server with id {guild_id} not found.")

def display_selfbots():
    bots = load_selfbots_data()
    print(f"\n--- Registered Bots ({len(bots)}) ---")
    if not bots:
        print("No bots found.")
    else:
        for bot_id, data in bots.items():
            print(f"ID: {bot_id} | Name: {data['Name']}")

def display_servers():
    servers = load_servers_data()
    print(f"\n--- Registered Servers ({len(servers)}) ---")
    if not servers:
        print("No servers found.")
    else:
        for server in servers:
            print(f"Server: {server['GuildName']} ({server['GuildId']}) -> Channel: {server['ChannelName']} ({server['ChannelId']})")

# ------------------- UTILS -----------------------------------

def get_yes_no_input(message: str) -> bool:
    while True:
        user_input = input(f"{message} [y/n]: ").strip().lower()
        if user_input == 'y':
            return True
        elif user_input == 'n':
            return False
        else:
            print("Invalid input. Please answer with 'y' or 'n'.")

def ensure_data_directory():
    directory = os.path.dirname(DATA_SELFBOTS)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
