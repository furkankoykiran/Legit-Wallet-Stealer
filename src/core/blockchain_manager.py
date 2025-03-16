import asyncio
import aiohttp
from web3 import Web3, AsyncWeb3
from typing import Dict, List, Optional
from cachetools import TTLCache
import ccxt.async_support as ccxt

from ..config import Config
from ..services.telegram_service import TelegramService
from ..utils.logger import get_logger

class BlockchainManager:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = Config()
        self.telegram = TelegramService(
            self.config.telegram_token,
            self.config.telegram_chat_id
        )
        
        # Initialize blockchain connections
        self.web3_clients: Dict[str, AsyncWeb3] = {}
        self._initialize_web3_clients()
        
        # Cache for token prices (2 minute TTL)
        self.price_cache = TTLCache(maxsize=1000, ttl=120)
        
        # Initialize exchange API for price data
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'asyncio_loop': asyncio.get_event_loop()
        })
        
        # Supported blockchain networks
        self.supported_chains = {
            'ETH': 1,  # Ethereum Mainnet
            'BSC': 56,  # Binance Smart Chain
            'POLYGON': 137,  # Polygon
            'AVALANCHE': 43114,  # Avalanche C-Chain
        }
        
        # Standard ERC20 ABI for token balance checks
        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]

    def _initialize_web3_clients(self) -> None:
        """Initialize Web3 clients for each supported blockchain"""
        for chain, rpc_url in self.config.rpc_endpoints.items():
            if rpc_url:
                try:
                    provider = AsyncWeb3.AsyncHTTPProvider(rpc_url)
                    self.web3_clients[chain] = AsyncWeb3(provider)
                except Exception as e:
                    self.logger.error(f"Failed to initialize {chain} client: {str(e)}")

    async def get_wallet_balance(
        self,
        address: str,
        chain_id: int
    ) -> Dict[str, float]:
        """Get wallet balance including native coin and major tokens"""
        chain = next(
            (k for k, v in self.supported_chains.items() if v == chain_id),
            None
        )
        if not chain or chain not in self.web3_clients:
            return {}

        web3 = self.web3_clients[chain]
        balances = {}

        try:
            # Check native coin balance
            balance = await web3.eth.get_balance(address)
            if balance > 0:
                balances[chain] = float(web3.from_wei(balance, 'ether'))

            # Check major token balances
            token_list = await self._get_major_tokens(chain)
            for token_addr, symbol in token_list.items():
                token_contract = web3.eth.contract(
                    address=Web3.to_checksum_address(token_addr),
                    abi=self.erc20_abi
                )
                token_balance = await token_contract.functions.balanceOf(address).call()
                if token_balance > 0:
                    decimals = await token_contract.functions.decimals().call()
                    balance = float(token_balance) / (10 ** decimals)
                    balances[symbol] = balance

            return balances

        except Exception as e:
            self.logger.error(f"Error checking {chain} balance: {str(e)}")
            return {}

    async def _get_major_tokens(self, chain: str) -> Dict[str, str]:
        """Get list of major tokens for the specified chain"""
        # This could be expanded to fetch from an API or database
        if chain == 'ETH':
            return {
                '0xdac17f958d2ee523a2206206994597c13d831ec7': 'USDT',
                '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': 'USDC',
                '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': 'WBTC',
            }
        elif chain == 'BSC':
            return {
                '0x55d398326f99059ff775485246999027b3197955': 'USDT',
                '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d': 'USDC',
                '0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c': 'BTCB',
            }
        return {}

    async def get_token_price(self, symbol: str) -> float:
        """Get token price in USD with caching"""
        try:
            # Check cache first
            if symbol in self.price_cache:
                return self.price_cache[symbol]

            # Fetch new price
            if symbol in ('ETH', 'BSC', 'POLYGON', 'AVALANCHE'):
                symbol = 'ETH' if symbol in ('ETH', 'POLYGON') else 'BNB'
            
            ticker = await self.exchange.fetch_ticker(f'{symbol}/USDT')
            price = ticker['last']
            
            # Cache the result
            self.price_cache[symbol] = price
            return price

        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {str(e)}")
            return 0.0

    async def calculate_total_value(self, balances: Dict[str, float]) -> float:
        """Calculate total USD value of all tokens"""
        total = 0.0
        for token, amount in balances.items():
            price = await self.get_token_price(token)
            total += amount * price
        return total

    async def close(self) -> None:
        """Close all connections"""
        await self.exchange.close()
        # Close web3 connections if needed
        for web3 in self.web3_clients.values():
            await web3.provider.close()