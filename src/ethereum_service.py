"""Module for handling Ethereum-related operations."""
import random
import torch
import numpy as np
from typing import Tuple, List, Optional
import os
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_utils import exceptions
from eth_keys import keys
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
        max_retries = 3
        retry_delay = 5
        last_error = None
        
        for attempt in range(max_retries):
            try:
                provider = Web3.HTTPProvider(
                    GETH_ENDPOINT,
                    request_kwargs={
                        'timeout': 60,  # Increased timeout
                        'headers': {
                            "Content-Type": "application/json",
                        }
                    }
                )
                web3 = Web3(provider)
                
                # Add PoA middleware for compatibility
                web3.middleware_onion.inject(geth_poa_middleware, layer=0)
                
                # Test connection
                if not web3.is_connected():
                    raise ConnectionError("Node is not responding")
                    
                # Verify sync status
                sync_status = web3.eth.syncing
                if sync_status is not False:
                    print(f"Warning: Node is still syncing - {sync_status}")
                
                print(f"Connected to Ethereum node at block {web3.eth.block_number:,}")
                return web3
                
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    print(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                
        raise ConnectionError(f"Failed to initialize Web3 after {max_retries} attempts: {last_error}")

    def _generate_private_key(self) -> bytes:
        """Generate a random private key."""
        return os.urandom(32)  # 256 bits

    def generate_random_mnemonic(self, word_list: List[str]) -> str:
        """Generate a valid private key and convert to address."""
        try:
            private_key = self._generate_private_key()
            account = Account.from_key(private_key)
            return account.address
        except Exception as e:
            print(f"Private key generation error: {e}")
            return None

    def generate_random_mnemonics_gpu(self, word_list: List[str], batch_size: int) -> List[str]:
        """Generate multiple private keys and convert to addresses using GPU for randomness."""
        try:
            addresses = []
            if self.device.type == "cuda":
                # Generate batch of random numbers on GPU
                random_tensor = torch.randint(
                    0, 256,
                    (batch_size, 32),  # 32 bytes for each private key
                    dtype=torch.uint8,
                    device=self.device
                )
                
                # Process in smaller chunks for efficiency
                chunk_size = 100
                for i in range(0, batch_size, chunk_size):
                    chunk = random_tensor[i:i+chunk_size].cpu().numpy()
                    for private_key_bytes in chunk:
                        try:
                            account = Account.from_key(bytes(private_key_bytes))
                            if account and account.address:
                                addresses.append(account.address)
                        except:
                            continue
                            
                    if len(addresses) >= batch_size:
                        break
                        
                # Return exact batch size
                return addresses[:batch_size]
            
            # Fallback to CPU generation
            while len(addresses) < batch_size:
                address = self.generate_random_mnemonic([])
                if address:
                    addresses.append(address)
                    
            return addresses
            
        except Exception as e:
            print(f"Batch key generation error: {e}")
            return []

    def check_wallet(self, address: str) -> Tuple[Optional[str], float]:
        """Check the balance of a wallet address."""
        try:
            if not address or not Web3.is_address(address):
                return None, 0.0
                
            # Get balance efficiently
            try:
                balance_wei = self.get_balance(address)
                if balance_wei > 0:
                    return address, float(self.from_wei(balance_wei, 'ether'))
                return address, 0.0
            except Exception as e:
                print(f"Balance check error for {address[:10]}...: {e}")
                return address, 0.0
                
        except Exception as e:
            print(f"Wallet check error: {e}")
            return None, 0.0

    def check_wallets_batch(self, addresses: List[str]) -> List[Tuple[Optional[str], float]]:
        """Check multiple wallet addresses in parallel."""
        try:
            # Filter valid addresses first
            valid_addresses = [addr for addr in addresses if addr and Web3.is_address(addr)]
            
            if not valid_addresses:
                return [(None, 0.0)] * len(addresses)
            
            # Create batch request for balances
            batch = [
                {
                    'jsonrpc': '2.0',
                    'method': 'eth_getBalance',
                    'params': [addr, 'latest'],
                    'id': i
                }
                for i, addr in enumerate(valid_addresses)
            ]
            
            try:
                # Send batch request
                response = self.web3.provider.make_request("eth_getBatch", [batch])
                
                if isinstance(response, list):
                    # Process responses
                    results = [(None, 0.0)] * len(addresses)  # Initialize with default values
                    
                    for i, (addr, resp) in enumerate(zip(valid_addresses, response)):
                        if 'result' in resp:
                            balance_wei = int(resp['result'], 16)
                            balance_eth = float(self.from_wei(balance_wei, 'ether'))
                            # Find original index
                            orig_idx = addresses.index(addr)
                            results[orig_idx] = (addr, balance_eth)
                            
                    return results
                    
            except Exception as e:
                print(f"Batch balance check failed: {e}")
            
            # Fallback to individual checks
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                return list(executor.map(self.check_wallet, addresses))
                
        except Exception as e:
            print(f"Batch processing error: {e}")
            return [(None, 0.0)] * len(addresses)

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