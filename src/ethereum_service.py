"""Module for handling Ethereum-related operations."""
import random
import torch
import numpy as np
from typing import Tuple, List, Optional
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_utils import exceptions
import concurrent.futures
from src.config import GETH_ENDPOINT, MNEMONIC_WORD_COUNT

class EthereumService:
    """Service class for Ethereum operations."""

    def __init__(self):
        """Initialize the Ethereum service with optimized Web3 configuration."""
        Account.enable_unaudited_hdwallet_features()
        
        # Initialize Web3 with proper connection handling and optimization
        self.web3 = self._initialize_web3()
        
        # Disable certain middleware for better performance
        self.web3.middleware_onion.remove('validation')
        
        # Pre-compile common Web3 operations
        self.from_wei = self.web3.from_wei
        self.get_balance = self.web3.eth.get_balance

        # Initialize GPU if available
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        if self.device.type == "cuda":
            # Initialize CUDA for better performance
            torch.cuda.init()
            # Warm up GPU
            self._warm_up_gpu()
        
    def _warm_up_gpu(self):
        """Warm up GPU with some initial computations."""
        try:
            # Run a few initial computations to warm up the GPU
            for _ in range(5):
                size = 1000
                a = torch.randn(size, size, device=self.device)
                b = torch.randn(size, size, device=self.device)
                torch.matmul(a, b)
            torch.cuda.synchronize()
        except Exception as e:
            print(f"GPU warm-up error (non-critical): {e}")

    def _initialize_web3(self) -> Web3:
        """Initialize and configure Web3 connection with optimizations."""
        try:
            provider = Web3.HTTPProvider(
                GETH_ENDPOINT,
                request_kwargs={
                    'timeout': 30,
                    'headers': {
                        "Content-Type": "application/json",
                    }
                }
            )
            web3 = Web3(provider)
            
            # Add PoA middleware for compatibility
            web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if not web3.is_connected():
                raise ConnectionError("Failed to connect to Ethereum node")
                
            if web3.eth.chain_id != 1:  # 1 is the chain ID for Ethereum mainnet
                raise ValueError("Not connected to Ethereum mainnet")
                
            return web3
            
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Web3: {str(e)}")

    def generate_random_mnemonic(self, word_list: List[str]) -> str:
        """Generate a random mnemonic phrase."""
        selected_words = random.sample(word_list, MNEMONIC_WORD_COUNT)
        return " ".join(selected_words)

    def generate_random_mnemonics_gpu(self, word_list: List[str], batch_size: int) -> List[str]:
        """Generate multiple random mnemonic phrases using GPU acceleration."""
        try:
            if self.device.type == "cuda":
                # Convert word list to tensor for GPU operations
                word_count = len(word_list)
                
                # Generate random indices on GPU
                with torch.cuda.device(self.device):
                    # Create a tensor of indices for each position in each mnemonic
                    indices = torch.empty(
                        (batch_size, MNEMONIC_WORD_COUNT),
                        dtype=torch.long,
                        device=self.device
                    )
                    
                    # Fill with random indices efficiently
                    for i in range(MNEMONIC_WORD_COUNT):
                        indices[:, i] = torch.randint(
                            0, word_count, (batch_size,),
                            device=self.device
                        )
                    
                    # Move to CPU and convert to numpy for word lookup
                    indices = indices.cpu().numpy()
                    
                torch.cuda.synchronize()  # Ensure GPU operations are complete
                
                # Convert indices to words using numpy for efficiency
                return [
                    " ".join(np.array(word_list)[indices[i]])
                    for i in range(batch_size)
                ]
        except Exception as e:
            print(f"GPU mnemonic generation error, falling back to CPU: {e}")
        
        # Fallback to CPU generation
        return [self.generate_random_mnemonic(word_list) for _ in range(batch_size)]

    def check_wallet(self, mnemonic: str) -> Tuple[Optional[str], float]:
        """Check the balance of a wallet generated from a mnemonic phrase."""
        try:
            # Generate account (this is CPU intensive)
            account = Account.from_mnemonic(mnemonic)
            address = account.address
            
            try:
                # Get balance (this is I/O intensive)
                balance_wei = self.get_balance(address)
                if balance_wei > 0:
                    return address, float(self.from_wei(balance_wei, 'ether'))
                return address, 0.0
                
            except (exceptions.ValidationError, 
                   exceptions.BlockNotFound, 
                   exceptions.TransactionNotFound):
                return None, 0.0
                
        except (exceptions.ValidationError, ValueError):
            return None, 0.0
        except Exception as e:
            print(f"Unexpected error checking wallet: {e}")
            return None, 0.0

    def check_wallets_batch(self, mnemonics: List[str]) -> List[Tuple[Optional[str], float]]:
        """Check multiple wallets in parallel for better performance."""
        # Use more threads when GPU is handling the computation
        max_workers = 32 if self.device.type == "cuda" else 10
        max_workers = min(max_workers, len(mnemonics))
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(self.check_wallet, mnemonics))