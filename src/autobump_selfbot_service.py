from dataclasses import dataclass
import logging
import discord
import asyncio
import threading
from typing import Optional

from src.disboard_embed_decoder import *

discord.utils.setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

DISBOARD_APPLICATION_ID = 302050872383242240
BUMP_SLASH_COMMAND_NAME = "bump"
DISBOARD_BOT_ID = 302050872383242240

@dataclass
class BumpResult:
    success: bool
    next_bump_delay_minutes: int
    
class AutoBumpSelfbotService:
    """
    Manages a Discord selfbot instance running in a separate background thread.

    This service provides a synchronous interface to interact with the asynchronous
    Discord client.

    Attributes
    ----------
    bot : discord.Client
        The Discord client instance.
    token : str
        The authentication token for the selfbot.
    listening_channel_id : int
        The ID of the channel where the bot expects a response from Disboard.
    """

    def __init__(self, token: str, connection_timeout: int = 30):
        """
        Initialize the selfbot service and start the background thread.

        Parameters
        ----------
        token : str
            The user token to authenticate with Discord.
        connection_timeout : int, optional
            The maximum number of seconds to wait for the bot to connect
            (default is 30).

        Raises
        ------
        Exception
            If the bot fails to connect within the timeout period.
        """

        self.bot = discord.Client()
        self.token = token
        self.listening_channel_id = -1
        
        # Event to know when the bot is ready to accept requests
        self._is_ready = threading.Event()

        # Event to know when the bot see a bump response
        self._bump_response_event = threading.Event()
        self._last_bump_result: Optional[BumpResult] = None

        # Thread configuration
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_bot, daemon=True)

        # Start the bot
        self._thread.start()

        logger.info("Waiting for Discord connection...")
        connected = self._is_ready.wait(timeout=connection_timeout)
        if not connected:
            raise Exception("Timeout: Could not connect to Discord. Check token or internet connection.")
        else:
            logger.info("DiscordService is ready!")

    def _run_bot(self):
        """
        Run the bot's event loop in the background thread.

        This handles the 'on_ready' and 'on_message' events.
        """

        asyncio.set_event_loop(self._loop)

        @self.bot.event
        async def on_ready():
            if not self._is_ready.is_set():
                logger.info(f'Logged in as {self.bot.user})')
                self._is_ready.set()

        @self.bot.event
        async def on_message(message: discord.Message):
            if message.channel.id != self.listening_channel_id or message.author.id != DISBOARD_BOT_ID:
                return
            
            interaction = message.interaction
            if interaction is None:
                return
            
            user = self.bot.user
            guild = message.guild
            if interaction.name != BUMP_SLASH_COMMAND_NAME or user is None or guild is None or interaction.user.id != user.id:
                return

            # message.flags.ephemeral

            embeds = message.embeds
            if embeds:
                embed = embeds[0]
                result = None
                if is_success_embed(embed, guild.id):
                    logger.info(f"Successfully bumped server '{guild.name}' on channel '{message.channel.name}'.")
                    result = BumpResult(success=True, next_bump_delay_minutes=120)
                else:
                    remaining_time = find_time_left(embed)
                    logger.info(f"Tried to bump '{guild.name}' on channel '{message.channel.name}', but server on cooldown ({remaining_time} minutes).")
                    result = BumpResult(success=False, next_bump_delay_minutes=remaining_time)

                if result is not None:
                    self._last_bump_result = result
                    self._bump_response_event.set()

        try:
            # We start the selfbot
            self._loop.run_until_complete(self.bot.start(self.token))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in selfbot execution: {e}")
        finally:
            self._cleanup_loop()

    def _cleanup_loop(self):
            """Cancel all pending tasks and close the asyncio loop safely."""
            try:
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
                
                # Let the tasks cancel themselves
                if pending:
                    self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                
                self._loop.close()
                logger.info("Bot thread cleaned up and closed.")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

    def _execute_async(self, coro):
        """
        Helper to run a coroutine in the bot's loop and wait for the result synchronously.

        Parameters
        ----------
        coro : Coroutine
            The coroutine to execute in the bot's event loop.

        Returns
        -------
        Any
            The result of the coroutine execution, or None if an error occurs.

        Raises
        ------
        Exception
            If the selfbot is not ready.
        """

        if not self._is_ready.is_set():
            raise Exception("Selbot is not ready yet.")
            
        # Submit the task to the bot's loop
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        
        try:
            # Wait for the result (blocking call)
            return future.result(timeout=10)
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None

#   ---------------------------- Public Methods --------------------------------

    def get_guild_name(self, guild_id: int) -> Optional[str]:
        """
        Retrieve the name of a specific guild (server).

        Parameters
        ----------
        guild_id : int
            The ID of the guild.

        Returns
        -------
        Optional[str]
            The name of the guild if found.
        """

        async def task():
            guild = self.bot.get_guild(guild_id)
            if guild:
                return guild.name
            
            try:
                guild = await self.bot.fetch_guild(guild_id)
                return guild.name
            except (discord.NotFound, discord.Forbidden):
                return None
        
        return self._execute_async(task())

    def get_channel_name(self, channel_id: int) -> Optional[str]:
        """
        Retrieve the name of a specific channel.

        Parameters
        ----------
        channel_id : int
            The ID of the channel.

        Returns
        -------
        Optional[str]
            The name of the channel if found.
        """

        async def task():
            channel = self.bot.get_channel(channel_id)
            if channel:
                return getattr(channel, "name", None)

            try:
                channel = await self.bot.fetch_channel(channel_id)
                return getattr(channel, "name", None)
            except Exception:
                return None
        
        return self._execute_async(task())
    
    def get_account_id_and_name(self) -> Optional[tuple[int, str]]:
        """
        Retrieve the ID and username of the current selfbot account.

        Returns
        -------
        Optional[tuple[int, str]]
            A tuple containing (user_id, user_name) if success.
        """

        async def task():
            user = self.bot.user
            if user is not None:
                return (user.id, user.name)
        
        return self._execute_async(task())
    
    def bump_server(self, channel_id: int) -> bool:
        """
        Trigger the Disboard /bump command in the specified channel.

        Parameters
        ----------
        channel_id : int
            The ID of the channel where the command should be sent.

        Returns
        -------
        bool
            True if the command was successfully triggered, False otherwise.
        """

        # reset result before sending
        self._bump_response_event.clear()
        self._last_bump_result = None

        async def task() -> bool:
            channel = await self.bot.fetch_channel(channel_id)
            if isinstance(channel, discord.TextChannel):

                command_list = [
                    cmd for cmd in await channel.application_commands() 
                    if cmd.name == BUMP_SLASH_COMMAND_NAME and cmd.application_id == DISBOARD_APPLICATION_ID
                ]

                if not command_list:
                    logger.error(f"Command {BUMP_SLASH_COMMAND_NAME} (ID: {DISBOARD_APPLICATION_ID}) not found.")
                    return False

                target_command = command_list[0]

                self.listening_channel_id = channel_id
                await target_command.__call__(channel=channel)
                return True

            return False

        res = self._execute_async(task())
        return res if isinstance(res, bool) else False
    

    def wait_for_bump_result(self, timeout: int = 10) -> Optional[BumpResult]:
        """
        Block execution until on_message receives the result or timeout occurs.
        """
        is_set = self._bump_response_event.wait(timeout=timeout)
        
        if is_set:
            return self._last_bump_result
        else:
            logger.warning("Timed out waiting for Disboard response.")
            return None


    def stop(self):
        """
        Stop the selfbot gracefully.

        Closes the Discord connection, terminates the event loop, and
        joins the background thread.
        """

        if not self._is_ready.is_set():
            return

        logger.info("Stopping bot...")
        
        # Ask the bot to close himself
        future = asyncio.run_coroutine_threadsafe(self.bot.close(), self._loop)
        
        try:
            # Wait for confirmation
            future.result(timeout=10)
        except Exception as e:
            logger.warning(f"Error closing bot gracefully: {repr(e)}")

        # Now that the bot has finished its 'start()' function, the thread will arrive
        # in the 'finally' block of _run_bot and terminate. We can join it.
        self._thread.join(timeout=5)
        logger.info("Service stopped.")
