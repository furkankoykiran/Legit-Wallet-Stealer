import asyncio
from typing import Optional
import aiohttp
from ..utils.logger import get_logger

class TelegramService:
    def __init__(self, token: str, chat_id: str):
        self.logger = get_logger(__name__)
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self) -> None:
        """Ensure aiohttp session is created"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def send_message(self, message: str) -> bool:
        """Send message to Telegram chat"""
        if not self.token or not self.chat_id:
            self.logger.error("Telegram token or chat ID not configured")
            return False

        try:
            await self._ensure_session()
            
            # Split message if it exceeds Telegram's limit
            max_length = 4096
            messages = [message[i:i+max_length] 
                       for i in range(0, len(message), max_length)]
            
            for msg_part in messages:
                async with self.session.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": msg_part,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True
                    }
                ) as response:
                    if response.status != 200:
                        error_data = await response.text()
                        self.logger.error(f"Telegram API error: {error_data}")
                        return False
                    
                    # Add small delay between messages to avoid rate limits
                    if len(messages) > 1:
                        await asyncio.sleep(0.1)
            
            return True

        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {str(e)}")
            return False

    async def close(self) -> None:
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()