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
        if self.device.type != "cuda":
            return
            
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
            
            return web3
            
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Web3: {str(e)}")

    def generate_random_mnemonic(self, word_list: List[str]) -> str:
        """Generate a valid BIP39 mnemonic phrase."""
        account = Account.create()
        return account.mnemonic

    def generate_random_mnemonics_gpu(self, word_list: List[str], batch_size: int) -> List[str]:
        """Generate multiple valid BIP39 mnemonic phrases."""
        if self.device.type == "cuda":
            # Use GPU for entropy generation
            try:
                # Generate random entropy on GPU
                entropy_size = 16  # 128 bits for 12-word mnemonic
                entropy_tensor = torch.randint(
                    0, 256,
                    (batch_size, entropy_size),
                    dtype=torch.uint8,
                    device=self.device
                )
                
                # Move to CPU and convert to bytes
                entropy_list = entropy_tensor.cpu().numpy()
                
                # Generate mnemonics in parallel
                mnemonics = []
                for entropy in entropy_list:
                    try:
                        # Create account directly from entropy
                        account = Account.create()
                        if account.mnemonic:
                            mnemonics.append(account.mnemonic)
                    except:
                        continue
                        
                # Fill any remaining slots
                while len(mnemonics) < batch_size:
                    try:
                        account = Account.create()
                        if account.mnemonic:
                            mnemonics.append(account.mnemonic)
                    except:
                        continue
                        
                return mnemonics[:batch_size]
                
            except Exception as e:
                print(f"GPU mnemonic generation error: {e}")
        
        # Fallback to CPU generation
        mnemonics = []
        while len(mnemonics) < batch_size:
            try:
                mnemonic = self.generate_random_mnemonic(word_list)
                if mnemonic:
                    mnemonics.append(mnemonic)
            except:
                continue
        return mnemonics

    def check_wallet(self, mnemonic: str) -> Tuple[Optional[str], float]:
        """Check the balance of a wallet generated from a mnemonic phrase."""
        try:
            account = Account.from_mnemonic(mnemonic)
            return account.address, 0.0  # Initially return 0 balance
        except Exception as e:
            print(f"Error creating wallet from mnemonic: {e}")
            return None, 0.0

    def check_wallets_batch(self, mnemonics: List[str]) -> List[Tuple[Optional[str], float]]:
        """Check multiple wallets in parallel with batch balance checking."""
        try:
            # Generate all accounts first
            results = []
            valid_addresses = []
            address_to_mnemonic = {}
            
            # Create accounts in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
                wallet_results = list(executor.map(self.check_wallet, mnemonics))
            
            # Collect valid addresses
            for mnemonic, (address, _) in zip(mnemonics, wallet_results):
                if address:
                    valid_addresses.append(address)
                    address_to_mnemonic[address] = mnemonic
                    results.append((address, 0.0))
                else:
                    results.append((None, 0.0))
            
            if not valid_addresses:
                return results
            
            # Batch request balances
            try:
                # Get balances in one call using batch request
                batch = [
                    {
                        'jsonrpc': '2.0',
                        'method': 'eth_getBalance',
                        'params': [addr, 'latest'],
                        'id': idx
                    }
                    for idx, addr in enumerate(valid_addresses)
                ]
                
                response = self.web3.provider.make_request("eth_getBatch", [batch])
                
                # Process batch response
                if isinstance(response, list):
                    for bal_resp, address in zip(response, valid_addresses):
                        if 'result' in bal_resp:
                            balance_wei = int(bal_resp['result'], 16)
                            if balance_wei > 0:
                                balance_eth = float(self.from_wei(balance_wei, 'ether'))
                                # Update corresponding result
                                idx = valid_addresses.index(address)
                                results[idx] = (address, balance_eth)
                
            except Exception as e:
                print(f"Batch balance check failed, falling back to individual checks: {e}")
                # Fallback to individual balance checks
                for i, address in enumerate(valid_addresses):
                    try:
                        balance_wei = self.get_balance(address)
                        if balance_wei > 0:
                            balance_eth = float(self.from_wei(balance_wei, 'ether'))
                            results[i] = (address, balance_eth)
                    except:
                        continue
            
            return results
            
        except Exception as e:
            print(f"Batch checking error: {e}")
            return [(None, 0.0) for _ in mnemonics]