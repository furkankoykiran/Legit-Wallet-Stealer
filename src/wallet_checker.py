"""Main module for the Ethereum wallet checking application."""
import socket
import multiprocessing
from multiprocessing import Value, Lock
import time
from typing import List
import torch
from colorama import Fore, Style, init
from src.config import load_word_list
from src.ethereum_service import EthereumService
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

def worker_process(worker_id: int, word_list: List[str], counter: SharedCounter, device: str):
    """Worker process for checking wallets."""
    try:
        ethereum = EthereumService()
        telegram = TelegramService()
        
        # Use larger batch size for GPU
        BATCH_SIZE = 200 if device == "cuda" else 50
        start_time = time.time()
        local_checked = 0
        
        # Pre-compile device specific components
        if device == "cuda":
            torch.cuda.init()
        
        while True:
            try:
                # Generate mnemonics in batches
                if device == "cuda":
                    # Use GPU for parallel mnemonic generation
                    mnemonics = ethereum.generate_random_mnemonics_gpu(
                        word_list, BATCH_SIZE
                    )
                else:
                    # CPU-based generation
                    mnemonics = [
                        ethereum.generate_random_mnemonic(word_list)
                        for _ in range(BATCH_SIZE)
                    ]
                
                # Check wallets in parallel
                results = ethereum.check_wallets_batch(mnemonics)
                
                # Process results
                for mnemonic, (address, balance) in zip(mnemonics, results):
                    if address and balance > 0:
                        message = (
                            f"[+] Found wallet with balance!\n"
                            f"Mnemonic: {mnemonic}\n"
                            f"Balance: {balance} ETH\n"
                            f"Address: {address}"
                        )
                        telegram.send_message(message)
                        return
                
                # Update counters
                local_checked += BATCH_SIZE
                total_checked = counter.increment(BATCH_SIZE)
                
                # Calculate and display performance metrics
                if local_checked % 1000 == 0:
                    elapsed_time = time.time() - start_time
                    wallets_per_second = local_checked / elapsed_time
                    status = (
                        f"{Fore.CYAN}Worker {worker_id:<2}{Style.RESET_ALL} | "
                        f"Speed: {format_number(wallets_per_second)} w/s | "
                        f"Checked: {Fore.BLUE}{total_checked:,}{Style.RESET_ALL}"
                    )
                    print(status)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"{Fore.RED}Worker {worker_id} error: {e}{Style.RESET_ALL}")
                continue
                
    except Exception as e:
        print(f"{Fore.RED}Worker {worker_id} initialization error: {e}{Style.RESET_ALL}")
    finally:
        if device == "cuda":
            torch.cuda.empty_cache()

class WalletChecker:
    """Main class for checking Ethereum wallets."""

    def __init__(self):
        """Initialize services and load word list."""
        self.word_list = load_word_list()
        self.telegram = TelegramService()
        self.counter = SharedCounter()
        self.system = SystemService()
        
        # Setup system
        self.device = self.system.check_gpu_availability()
        self.worker_count = self.system.get_optimal_worker_count()

    def start(self):
        """Start the wallet checking processes."""
        # Ensure Geth is running if using local node
        if "127.0.0.1" in os.getenv("GETH_ENDPOINT", ""):
            if not self.system.ensure_geth_running():
                print(f"{Fore.RED}Failed to ensure Geth is running. "
                      f"Please start Geth manually.{Style.RESET_ALL}")
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
            # Create and start worker processes
            for i in range(self.worker_count):
                p = multiprocessing.Process(
                    target=worker_process,
                    args=(i, self.word_list, self.counter, self.device.type)
                )
                processes.append(p)
                p.start()

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