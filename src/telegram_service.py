"""Module for sending Telegram notifications."""
import requests
import logging
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class TelegramService:
    """Service for sending Telegram notifications."""
    
    def __init__(self):
        """Initialize the Telegram service."""
        self.enabled = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
        if not self.enabled:
            logging.info("Telegram notifications disabled - no credentials provided")
            return
            
        self.base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
        self._test_connection()

    def _test_connection(self):
        """Test the Telegram connection."""
        if not self.enabled:
            return
            
        try:
            response = requests.get(
                f"{self.base_url}/getMe",
                timeout=5
            )
            if not response.ok:
                logging.warning("Telegram connection test failed")
                self.enabled = False
        except Exception as e:
            logging.warning(f"Telegram connection error: {e}")
            self.enabled = False

    def send_message(self, message: str) -> bool:
        """
        Send a message via Telegram.
        
        Args:
            message (str): Message to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            logging.info(f"Telegram disabled - would have sent: {message}")
            return False
            
        try:
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            return response.ok
        except Exception as e:
            logging.error(f"Error sending Telegram message: {e}")
            return False