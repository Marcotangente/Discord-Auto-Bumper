import os
import time
from dotenv import load_dotenv

from src.bump_scheduler import BumpScheduler
import src.json_manager as json_manager
import src.autobump_selfbot_service as abs_service

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = 1396626329129975849
GUILD_ID = 1332415672138858587


data_manager = json_manager.DataManager()

bmp = BumpScheduler(data_manager)

bmp.loop()


# while True:
#     print("\n=== CONFIG MANAGER ===")
#     print("1. Display Selfbots")
#     print("2. Register Selfbot")
#     print("3. Remove Selfbot")
#     print("4. Display Servers")
#     print("5. Register/Update Server")
#     print("6. Remove Server")
#     print("0. Exit")
    
#     choice = input("Select an option: ").strip()

#     if choice == "1":
#         json_manager.display_selfbots()
#     elif choice == "2":
#         b_id = input("Discord ID: ")
#         token = input("Account token: ")
#         name = input("Name: ")
#         json_manager.register_selfbot_json(b_id, token, name)
#     elif choice == "3":
#         b_id = input("Selfbot ID to remove: ")
#         json_manager.remove_selfbot(b_id)
#     elif choice == "4":
#         json_manager.display_servers()
#     elif choice == "5":
#         g_id = input("Server ID: ")
#         g_name = input("Server Name: ")
#         c_id = input("Channel ID: ")
#         c_name = input("Channel Name: ")
#         json_manager.register_server_json(g_id, g_name, c_id, c_name)
#     elif choice == "6":
#         g_id = input("Server ID to remove: ")
#         json_manager.remove_server(g_id)
#     elif choice == "0":
#         print("Goodbye!")
#         break
#     else:
#         print("Invalid option.")