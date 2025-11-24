import logging
import discord
import asyncio
import threading
from typing import Optional, Tuple

discord.utils.setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoBumpService:
    def __init__(self, token: str, connection_timeout: int = 30):

        self.bot = discord.Client()
        self.token = token
        
        # Event to know when the bot is ready to accept requests
        self._is_ready = threading.Event()

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
        asyncio.set_event_loop(self._loop)

        @self.bot.event
        async def on_ready():
            if not self._is_ready.is_set():
                logger.info(f'Logged in as {self.bot.user} (ID: {self.bot.user.id})')
                self._is_ready.set()

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
            # We need to clean the remaining tasks
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
        Helper to run a coroutine in the bot's loop and wait for the result
        synchronously.
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
    
    def get_accound_id_and_name(self) -> Optional[tuple[int, str]]:
        async def task():
            user = self.bot.user
            if user is not None:
                return (user.id, user.name)
        
        return self._execute_async(task())


    def stop(self):
        if not self._is_ready.is_set():
            return

        logger.info("Stopping bot...")
        
        # Ask the bot to close himself
        future = asyncio.run_coroutine_threadsafe(self.bot.close(), self._loop)
        
        try:
            # Wait for confirmation
            future.result(timeout=10)
        except Exception as e:
            logger.warning(f"Error closing bot gracefully: {e}")

        # Now that the bot has finished its 'start()' function, the thread will arrive
        # in the 'finally' block of _run_bot and terminate. We can join it.
        self._thread.join(timeout=5)
        logger.info("Service stopped.")
