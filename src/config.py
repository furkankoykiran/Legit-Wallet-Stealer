import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Configuration settings for the application"""
    
    def __init__(self):
        # Telegram settings
        self.telegram_token: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id: str = os.getenv('TELEGRAM_CHAT_ID', '')
        
        # Performance settings
        self.batch_size: int = int(os.getenv('BATCH_SIZE', '1000'))  # Number of wallets to check in parallel
        self.num_gpu_streams: int = int(os.getenv('NUM_GPU_STREAMS', '4'))  # Number of GPU streams
        self.check_interval: int = int(os.getenv('CHECK_INTERVAL', '60'))  # Seconds between checks
        
        # Blockchain settings
        self.rpc_endpoints: dict = {
            'ETH': os.getenv('ETH_RPC_URL', 'https://eth-mainnet.g.alchemy.com/v2/your-api-key'),
            'BSC': os.getenv('BSC_RPC_URL', 'https://bsc-dataseed.binance.org/'),
            'POLYGON': os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com'),
            'AVALANCHE': os.getenv('AVALANCHE_RPC_URL', 'https://api.avax.network/ext/bc/C/rpc'),
        }
        
        # API settings
        self.coingecko_api_url: str = 'https://api.coingecko.com/api/v3'
        self.min_token_value_usd: float = float(os.getenv('MIN_TOKEN_VALUE_USD', '10.0'))
        
        # System settings
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        self.enable_gpu: bool = os.getenv('ENABLE_GPU', 'true').lower() == 'true'
        
    def validate(self) -> None:
        """Validate configuration settings"""
        if not self.telegram_token or not self.telegram_chat_id:
            raise ValueError("Telegram token and chat ID are required")
        
        if self.batch_size < 1:
            raise ValueError("Batch size must be positive")
            
        if self.check_interval < 1:
            raise ValueError("Check interval must be positive")
        
        if not any(self.rpc_endpoints.values()):
            raise ValueError("At least one RPC endpoint must be configured")