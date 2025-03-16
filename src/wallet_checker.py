"""Main module for the Ethereum wallet checking application."""
import socket
import multiprocessing
from multiprocessing import Value, Lock
import time
from typing import List
import torch
from web3 import Web3
from colorama import Fore, Style, init
from src.config import load_system_config
from src.ethereum_service import EthereumService
import random
from src.telegram_service import TelegramService
from src.system_service import SystemService
import os

# Initialize colorama
init()

class SharedCounter:
    """Thread-safe counter for tracking total checked wallets."""
    
    def __init__(self):
        """Initialize the counter with a lock."""
        self._value = Value('i', 0)
        self._lock = Lock()
    
    def increment(self, amount: int = 1) -> int:
        """Increment counter by amount and return new value."""
        with self._lock:
            self._value.value += amount
            return self._value.value
            
    @property
    def value(self) -> int:
        """Get current counter value."""
        return self._value.value

def format_number(num: float) -> str:
    """Format number with commas and color based on value."""
    if num > 200:
        color = Fore.GREEN
    elif num > 100:
        color = Fore.YELLOW
    else:
        color = Fore.RED
    return f"{color}{num:,.2f}{Style.RESET_ALL}"

def worker_process(worker_id: int, counter: SharedCounter, device: str):
    """Worker process for checking wallets."""
    # Initialize variables
    start_time = time.time()
    local_checked = 0
    ethereum = None
    max_retries = 5

    # Initialize services with retry
    for attempt in range(max_retries):
        try:
            print(f"{Fore.YELLOW}Worker {worker_id} connecting to Ethereum node (attempt {attempt + 1}/{max_retries})...{Style.RESET_ALL}")
            ethereum = EthereumService()
            telegram = TelegramService()
            # Test connection
            w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
            if not w3.is_connected():
                raise ConnectionError("Node not responding")
            print(f"{Fore.GREEN}Worker {worker_id} connected successfully{Style.RESET_ALL}")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                retry_delay = random.uniform(1, 3) * (attempt + 1)  # Randomized exponential backoff
                print(f"{Fore.RED}Worker {worker_id} initialization failed: {e}, retrying in {retry_delay:.1f}s...{Style.RESET_ALL}")
                time.sleep(retry_delay)
            else:
                print(f"{Fore.RED}Worker {worker_id} failed to initialize after {max_retries} attempts{Style.RESET_ALL}")
                return

    try:
        
        # Calculate optimal batch size based on memory
        if device == "cuda":
            total_memory = torch.cuda.get_device_properties(0).total_memory
            BATCH_SIZE = min(2000, max(500, int(total_memory / (1024 * 1024 * 1024) * 200)))
            
            # Configure CUDA for this process
            torch.cuda.empty_cache()
            torch.backends.cudnn.benchmark = True
            torch.cuda.set_per_process_memory_fraction(0.8)
            
            # Generate first batch immediately
            mnemonics = ethereum.generate_random_mnemonics_gpu([], BATCH_SIZE)
            if mnemonics:
                print(f"{Fore.GREEN}Worker {worker_id} initialized with {len(mnemonics)} mnemonics{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Worker {worker_id} initialization retry...{Style.RESET_ALL}")
        else:
            BATCH_SIZE = 50
        
        mnemonic_buffer = []
        
        while True:
            try:
                # Refill buffer if needed
                if len(mnemonic_buffer) < BATCH_SIZE:
                    if device == "cuda":
                        # Generate larger batch for GPU efficiency
                        new_addresses = ethereum.generate_random_mnemonics_gpu([], BATCH_SIZE * 2)
                        if new_addresses:
                            mnemonic_buffer.extend(new_addresses)
                    else:
                        # CPU generation
                        while len(mnemonic_buffer) < BATCH_SIZE:
                            address = ethereum.generate_random_mnemonic([])
                            if address:
                                mnemonic_buffer.append(address)
                
                # Get current batch
                current_batch = mnemonic_buffer[:BATCH_SIZE]
                mnemonic_buffer = mnemonic_buffer[BATCH_SIZE:]
                
                if not current_batch:
                    if device == "cuda":
                        print(f"{Fore.YELLOW}Worker {worker_id} regenerating addresses...{Style.RESET_ALL}")
                    continue
                
                # Process batch
                results = ethereum.check_wallets_batch(current_batch)
                batch_success = 0
                
                # Process results efficiently
                for address, (valid_address, balance) in zip(current_batch, results):
                    if valid_address:
                        batch_success += 1
                        if balance > 0:
                            message = (
                                f"[+] Found wallet with balance!\n"
                                f"Address: {address}\n"
                                f"Balance: {balance} ETH"
                            )
                            telegram.send_message(message)
                            return
                
                # Update statistics for all processed wallets
                local_checked += len(current_batch)
                total_checked = counter.increment(len(current_batch))
                    
                elapsed_time = time.time() - start_time
                wallets_per_second = local_checked / elapsed_time
                
                # Show progress every 100 wallets
                if local_checked % 100 == 0:
                    status = (
                        f"{Fore.CYAN}Worker {worker_id:<2}{Style.RESET_ALL} | "
                        f"Speed: {format_number(wallets_per_second)} w/s | "
                        f"Valid: {batch_success}/{len(current_batch)} | "
                        f"Total: {Fore.BLUE}{total_checked:,}{Style.RESET_ALL}"
                    )
                    print(status)
                
                # Start generating next batch while processing current one
                if device == "cuda" and len(mnemonic_buffer) < BATCH_SIZE:
                    next_batch = ethereum.generate_random_mnemonics_gpu([], BATCH_SIZE)
                    if next_batch:
                        mnemonic_buffer.extend(next_batch)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"{Fore.RED}Worker {worker_id} error: {e}{Style.RESET_ALL}")
                time.sleep(0.1)  # Brief pause on error
                continue
                
    except Exception as e:
        print(f"{Fore.RED}Worker {worker_id} initialization error: {e}{Style.RESET_ALL}")
    finally:
        if device == "cuda":
            torch.cuda.empty_cache()

class WalletChecker:
    """Main class for checking Ethereum wallets."""

    def __init__(self):
        """Initialize services and system configuration."""
        self.config = load_system_config()
        self.telegram = TelegramService()
        self.counter = SharedCounter()
        self.system = SystemService()
        
        # Setup system
        self.device = self.system.check_gpu_availability()
        self.worker_count = min(16, self.system.get_optimal_worker_count())  # Limit workers
        
        if self.device.type == "cuda":
            # Configure CUDA settings
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            # Pre-allocate GPU memory
            self._prepare_gpu()
            
    def _prepare_gpu(self):
        """Prepare GPU for optimal performance."""
        try:
            # Set optimal GPU memory allocation
            torch.cuda.empty_cache()
            
            # Reserve GPU memory
            memory_pool = []
            try:
                while True:
                    memory_pool.append(torch.empty(256, 256, device="cuda"))
            except Exception:
                pass
            
            # Clear the pool but maintain the memory allocation
            del memory_pool
            torch.cuda.empty_cache()
            
            # Warm up CUDA kernels
            for _ in range(3):
                dummy_tensor = torch.randn(1000, 1000, device="cuda")
                torch.matmul(dummy_tensor, dummy_tensor.t())
            torch.cuda.synchronize()
            
        except Exception as e:
            print(f"GPU preparation error (non-critical): {e}")

    def start(self):
        """Start the wallet checking processes."""
        # Ensure Geth is running and synced
        try:
            print(f"{Fore.YELLOW}Waiting for Geth to be ready...{Style.RESET_ALL}")
            w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
            
            # Wait for Geth to be ready
            start_wait = time.time()
            while time.time() - start_wait < 300:  # 5 minutes timeout
                try:
                    if w3.is_connected() and w3.eth.syncing is False:
                        print(f"{Fore.GREEN}Geth is ready! Current block: {w3.eth.block_number:,}{Style.RESET_ALL}")
                        break
                except:
                    pass
                print("Waiting for Geth sync... (press Ctrl+C to cancel)")
                time.sleep(5)
            else:
                print(f"{Fore.RED}Geth connection timeout after 5 minutes.{Style.RESET_ALL}")
                return
                
        except Exception as e:
            print(f"{Fore.RED}Failed to connect to Geth: {e}{Style.RESET_ALL}")
            return

        # Send initial notification
        hostname = socket.gethostname()
        gpu_info = f" with GPU ({torch.cuda.get_device_name(0)})" if self.device.type == "cuda" else ""
        self.telegram.send_message(
            f"Wallet checker started on {hostname}{gpu_info}\n"
            f"Running with {self.worker_count} workers"
        )

        # Start worker processes
        processes: List[multiprocessing.Process] = []
        start_time = time.time()
        
        try:
            # Create and start worker processes with delay
            for i in range(self.worker_count):
                p = multiprocessing.Process(
                    target=worker_process,
                    args=(i, self.counter, self.device.type)
                )
                processes.append(p)
                p.start()
                # Small delay between worker starts to prevent GPU memory contention
                if self.device.type == "cuda":
                    time.sleep(0.5)

            # Monitor and display overall progress
            try:
                while any(p.is_alive() for p in processes):
                    time.sleep(5)  # Update every 5 seconds
                    elapsed_time = time.time() - start_time
                    total_checked = self.counter.value
                    overall_speed = total_checked / elapsed_time
                    active_workers = sum(1 for p in processes if p.is_alive())
                    
                    print("\n" + "═" * 50)
                    print(f"{Fore.GREEN}Overall Performance Summary{Style.RESET_ALL}")
                    print("═" * 50)
                    print(f"Device: {Fore.CYAN}{self.device.type.upper()}{Style.RESET_ALL}")
                    print(f"Total Wallets: {Fore.BLUE}{total_checked:,}{Style.RESET_ALL}")
                    print(f"Speed: {format_number(overall_speed)} wallets/sec")
                    print(f"Active Workers: {Fore.CYAN}{active_workers}/{self.worker_count}{Style.RESET_ALL}")
                    print("═" * 50 + "\n")
            
            except KeyboardInterrupt:
                raise
                    
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Stopping workers...{Style.RESET_ALL}")
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join()
            
            # Final statistics
            elapsed_time = time.time() - start_time
            total_checked = self.counter.value
            overall_speed = total_checked / elapsed_time
            
            print("\n" + "═" * 50)
            print(f"{Fore.GREEN}Final Statistics{Style.RESET_ALL}")
            print("═" * 50)
            print(f"Device: {Fore.CYAN}{self.device.type.upper()}{Style.RESET_ALL}")
            print(f"Runtime: {Fore.BLUE}{elapsed_time:.2f} seconds{Style.RESET_ALL}")
            print(f"Checked: {Fore.BLUE}{total_checked:,}{Style.RESET_ALL} wallets")
            print(f"Speed: {format_number(overall_speed)} wallets/sec")
            print("═" * 50)
            print(f"\n{Fore.GREEN}Workers stopped successfully{Style.RESET_ALL}")