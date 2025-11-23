import json
import multiprocessing
import os
import queue
import src.resolver_selfbot as resolver_selfbot

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DATA_SELFBOTS_RELATIVE = "data/selfbots.json"
DATA_SERVERS_RELATIVE = "data/servers.json"

DATA_SELFBOTS = os.path.join(PROJECT_ROOT, DATA_SELFBOTS_RELATIVE)
DATA_SERVERS = os.path.join(PROJECT_ROOT, DATA_SERVERS_RELATIVE)

def load_selfbots_data() -> dict[str, dict]:
    if os.path.exists(DATA_SELFBOTS):
        with open(DATA_SELFBOTS, "r", encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Error while loading {DATA_SELFBOTS}")
                return {}
    return {}

def load_servers_data() -> list:
    if os.path.exists(DATA_SERVERS):
        with open(DATA_SERVERS, "r", encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Error while loading {DATA_SERVERS}")
                return []
    return []

def register_selfbot(token: str):
    result_queue = multiprocessing.Queue()
    bot_process = multiprocessing.Process(target=resolver_selfbot.run_get_accound_id_and_name, args=(token, result_queue))

    bot_process.start()
    try:
        res = result_queue.get(timeout=15)
    except queue.Empty:
        res = (None, None)
        if bot_process.is_alive():
            bot_process.terminate()
    bot_process.join()

    id = res[0]
    id_str = str(id)
    name = res[1]

    if id is None or name is None:
        print("Error while registering selfbot.")
        return

    bots = load_selfbots_data()
    should_save = False

    if id_str in bots:
        if bots[id_str]["Name"] == name:
            print(f"The selfbot {name} is already registered.")
        else:
            print(f"Updated the name of the selfbot with id {id} ({bots[id_str]["Name"]} -> {name}).")
            bots[id_str]["Name"] = name
            should_save = True
    else:
        bots[id_str] = {
            "Token": token,
            "Name": name
        }
        print(f"Selfot {name} (ID: {id}) successfully saved.")
        should_save = True

    if should_save:
        ensure_data_directory()
        with open(DATA_SELFBOTS, "w", encoding='utf-8') as file:
            json.dump(bots, file, indent=4)


def register_server(guild_id: int, channel_id: int):
    selfbots = load_selfbots_data()
    first_bot = next(iter(selfbots.values()), None)
    if first_bot is None:
        print("There is no registered selfbot, please register a selfbot before.")
        return

    token = first_bot["Token"]

    result_queue = multiprocessing.Queue()
    bot_process = multiprocessing.Process(target=resolver_selfbot.run_get_guild_name_and_channel_name, args=(token, guild_id, channel_id, result_queue))
    bot_process.start()
    try:
        res = result_queue.get(timeout=15)
    except queue.Empty:
        res = (None, None)
        if bot_process.is_alive():
            bot_process.terminate()
    bot_process.join()

    guild_name = res[0]
    channel_name = res[1]

    if guild_name is None:
        print(f"Server with id {guild_id} not found.")
        remove_server(guild_id, False)
        return

    if channel_name is None:
        print(f"Channel with id {channel_id} not found.")

    should_save = False
    servers = load_servers_data()
    existing_server = next((server for server in servers if server["GuildId"] == guild_id), None)
    if existing_server is None:

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

        should_save = True

    else:
        if existing_server["GuildName"] != guild_name:
            print(f"Updated the name of server {guild_id} ! ({existing_server['GuildName']} -> {guild_name})")
            existing_server["GuildName"] = guild_name
            should_save = True

        if channel_name is None:
            print(f"Server {guild_name} is already registered. No changes were made.")

        elif existing_server["ChannelId"] != channel_id:
            if get_yes_no_input(f"The server {guild_id} is already registered. Do you want to replace the channel {existing_server['ChannelName']} by {channel_name} ?"):
                print(f"Server {guild_name} successfully updated ! ({existing_server['ChannelName']} -> {channel_name})")
                existing_server["ChannelId"] = channel_id
                existing_server["ChannelName"] = channel_name
                should_save = True
            else:
                print("Operation cancelled.")
        else:
            if existing_server["ChannelName"] != channel_name:
                print(f"Updated the name of the channel in {guild_name} ! ({existing_server['ChannelName']} -> {channel_name})")
                existing_server["ChannelName"] = channel_name
                should_save = True
            else:
                print(f"Server {guild_name} with channel {channel_name} is already registered.")

    if should_save:
        ensure_data_directory()
        with open(DATA_SERVERS, "w", encoding='utf-8') as file:
            json.dump(servers, file, indent=4)



def remove_selfbot(selfbot_id: str, feedback: bool = True):
    selfbots = load_selfbots_data()
    if selfbot_id in selfbots:
        removed_bot = selfbots.pop(selfbot_id)
        ensure_data_directory()
        with open(DATA_SELFBOTS, "w", encoding='utf-8') as file:
            json.dump(selfbots, file, indent=4)
        if feedback:
            print(f"Selfbot {removed_bot['Name']} (ID: {selfbot_id}) successfully removed.")
    elif feedback:
        print(f"Selbot with id {selfbot_id} not found.")

def remove_server(guild_id: int, feedback: bool = True):
    servers = load_servers_data()
    initial_count = len(servers)
    servers[:] = [server for server in servers if server["GuildId"] != guild_id]
    removed_count = initial_count - len(servers)
    if removed_count > 0:
        ensure_data_directory()
        with open(DATA_SERVERS, "w", encoding='utf-8') as file:
            json.dump(servers, file, indent=4)
        if feedback:
            print(f"Server with id {guild_id} successfully removed.")
    elif feedback:
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
