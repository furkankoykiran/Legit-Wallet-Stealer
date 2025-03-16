"""GPU-accelerated wallet management and checking module."""

import gc
import logging
from dataclasses import dataclass
from typing import List, Optional

import torch
import torch.multiprocessing as mp
from eth_account import Account
from web3 import Web3
from web3.exceptions import TransactionNotFound

from .config import GPUConfig
from .telegram_notifier import WalletInfo, get_notifier

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Enable HDWallet features
Account.enable_unaudited_hdwallet_features()

@dataclass
class WordList:
    """Container for mnemonic word list."""
    words: List[str]
    tensor: Optional[torch.Tensor] = None
    
    @classmethod
    def from_file(cls, filepath: str) -> 'WordList':
        """Load word list from file."""
        with open(filepath, "r", encoding="utf-8") as f:
            words = [line.strip() for line in f if line.strip()]
        return cls(words)

class WalletManager:
    """Manages wallet generation and balance checking with GPU acceleration."""
    
    def __init__(
        self,
        word_list: WordList,
        config: GPUConfig,
        web3: Optional[Web3] = None
    ):
        """Initialize wallet manager with optimized settings."""
        self.word_list = word_list
        self.config = config
        self.web3 = web3 or Web3()
        
        # Initialize word tensor on GPU
        self.device = torch.device("cuda")  # Always use CUDA
        if self.word_list.tensor is None:
            self.word_list.tensor = torch.tensor(
                range(len(word_list.words)),
                device=self.device,
                dtype=torch.long
            )

    @torch.no_grad()  # Disable gradient tracking for efficiency
    def _generate_mnemonics_batch(self) -> List[str]:
        """Generate optimized batch of random mnemonic phrases."""
        # Generate random indices in parallel on GPU
        indices = torch.randint(
            0,
            len(self.word_list.words),
            (self.config.batch_size, 12),
            device=self.device,
            dtype=torch.long
        )
        
        # Convert to words efficiently
        mnemonics = []
        for idx in indices:
            words = [self.word_list.words[i.item()] for i in idx]
            mnemonics.append(" ".join(words))
            
        # Clear CUDA cache periodically
        torch.cuda.empty_cache()
            
        return mnemonics

    def check_wallet_batch(self, mnemonic: str) -> Optional[WalletInfo]:
        """Optimized wallet balance checker."""
        try:
            account = Account.from_mnemonic(mnemonic)
            balance = float(self.web3.eth.get_balance(account.address))
            
            if balance > 0:
                return WalletInfo(
                    address=account.address,
                    balance=balance,
                    mnemonic=mnemonic
                )
                
        except (TransactionNotFound, ValueError):
            pass
            
        return None

    def process_worker(self, worker_id: int):
        """Optimized worker process."""
        notifier = get_notifier()
        checked = 0
        report_interval = 100000  # Reduced logging frequency
        
        while True:
            try:
                mnemonics = self._generate_mnemonics_batch()
                
                for mnemonic in mnemonics:
                    result = self.check_wallet_batch(mnemonic)
                    checked += 1
                    
                    if result:
                        notifier.notify_wallet_found(result)
                    
                    if checked % report_interval == 0:
                        # Memory cleanup
                        torch.cuda.empty_cache()
                        gc.collect()
                        
            except KeyboardInterrupt:
                break
                
        logger.warning("Worker %d finished: %d wallets", worker_id, checked)

    def start_processing(self):
        """Start optimized parallel processing."""
        processes = []
        
        try:
            # Start workers
            for i in range(self.config.num_workers):
                p = mp.Process(target=self.process_worker, args=(i,))
                p.start()
                processes.append(p)

            # Wait for completion
            for p in processes:
                p.join()
                
        except KeyboardInterrupt:
            for p in processes:
                p.terminate()
                p.join()
            
        finally:
            # Cleanup
            torch.cuda.empty_cache()
            gc.collect()