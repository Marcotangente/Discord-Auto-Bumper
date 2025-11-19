import discord
import re

DISBOARD_LINK = "https://disboard.org/"

def is_success_embed(embed: discord.Embed, guild_id) -> bool:
    dict = embed.to_dict()
    description = dict.get("description")
    if description is None:
        return False
    server_link = DISBOARD_LINK + "server/" + str(guild_id)
    return server_link in description

def find_time_left(embed: discord.Embed) -> int:
    dict = embed.to_dict()
    description = dict.get("description")
    if description is None:
        return -1
    return extract_minutes(description)

def extract_minutes(text):
    pattern = r"(\d+)\s+minutes"

    match = re.search(pattern, text)

    if match:
        minutes_str = match.group(1)
        minutes_value = int(minutes_str)
        return minutes_value
    else:
        return -1
