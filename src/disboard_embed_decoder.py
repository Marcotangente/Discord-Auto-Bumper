import discord
import re

DISBOARD_LINK = "https://disboard.org/"

def is_success_embed(embed: discord.Embed, guild_id: int) -> bool:
    """
    Check if an embed from disboard is a success message from a bump.
    
    Parameters
    ----------
    embed : discord.Embed
        An embed sent from disboard (reply of /bump command).
    guild_id : int
        The id of the bumped guild.

    Returns
    -------
    bool
        True if bump success, False otherwise.
    """

    embed_dict = embed.to_dict()
    description = embed_dict.get("description")
    if description is None:
        return False
    server_link = DISBOARD_LINK + "server/" + str(guild_id)
    return server_link in description

def find_time_left(embed: discord.Embed) -> int:
    """
    Find the time until next bump in an embed
    
    Parameters
    ----------
    embed : discord.Embed
        An embed sent from disboard (reply of /bump command).

    Returns
    -------
    int
        The time in minutes until next bump if found, -1 otherwise.
    """

    dict = embed.to_dict()
    description = dict.get("description")
    if description is None:
        return -1
    return _extract_minutes(description)

def _extract_minutes(text):
    """Extract the integer value of minutes from a text using regex."""
    pattern = r"(\d+)\s+minutes"

    match = re.search(pattern, text)

    if match:
        minutes_str = match.group(1)
        minutes_value = int(minutes_str)
        return minutes_value
    else:
        return -1
