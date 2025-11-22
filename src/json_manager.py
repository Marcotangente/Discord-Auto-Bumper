import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DATA_BOTS_RELATIVE = "data/bots.json"
DATA_CHANNELS_RELATIVE = "data/channels.json"

DATA_BOTS = os.path.join(PROJECT_ROOT, DATA_BOTS_RELATIVE)
DATA_CHANNELS = os.path.join(PROJECT_ROOT, DATA_CHANNELS_RELATIVE)

def load_bots_data() -> dict:
    if os.path.exists(DATA_BOTS):
        with open(DATA_BOTS, "r", encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Error while loading {DATA_BOTS}")
                return {}
    return {}

def load_channels_data() -> list:
    if os.path.exists(DATA_CHANNELS):
        with open(DATA_CHANNELS, "r", encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Error while loading {DATA_CHANNELS}")
                return []
    return []

def register_bot(bot_id: str, token: str, name: str):
    bots = load_bots_data()
    should_save = False 

    if bot_id in bots:
        if get_yes_no_input(f"The bot with ID {bot_id} already exists, do you want to replace it?"):
            bots[bot_id]["Token"] = token
            bots[bot_id]["Name"] = name
            should_save = True
        else:
            print("Operation cancelled.")
    else:
        bots[bot_id] = {
            "Token": token,
            "Name": name
        }
        should_save = True

    if should_save:
        with open(DATA_BOTS, "w", encoding='utf-8') as file:
            json.dump(bots, file, indent=4)
        print(f"Bot {name} (ID: {bot_id}) successfully saved.")

def register_channel(channel_id: str, channel_name: str):
    channels = load_channels_data()

    if not any(channel["Id"] == channel_id for channel in channels):
        channel_dic = {
            "Id": channel_id,
            "Name": channel_name
        }
        channels.append(channel_dic)

        with open(DATA_CHANNELS, "w", encoding='utf-8') as file:
            json.dump(channels, file, indent=4)
        print(f"Channel {channel_name} (ID: {channel_id}) successfully saved.")

    else:
        print(f"The channel with id {channel_id} already exists.")


########################################################""

def get_yes_no_input(message: str) -> bool:
    while True:
        user_input = input(f"{message} [y/n]: ").strip().lower()
        if user_input == 'y':
            return True
        elif user_input == 'n':
            return False
        else:
            print("Invalid input. Please answer with 'y' or 'n'.")