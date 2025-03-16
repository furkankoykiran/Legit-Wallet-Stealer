"""Entry point for the Ethereum wallet checker application."""
import multiprocessing
from src.wallet_checker import WalletChecker
import colorama
from colorama import Fore, Style

# Set multiprocessing start method to 'spawn' for CUDA compatibility
multiprocessing.set_start_method('spawn', force=True)

def main():
    """Main entry point of the application."""
    colorama.init()  # Initialize colorama for Windows compatibility
    try:
        print(f"{Fore.CYAN}╔═══════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║      Ethereum Wallet Checker Started      ║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╚═══════════════════════════════════════════╝{Style.RESET_ALL}")
        
        checker = WalletChecker()
        checker.start()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Application stopped by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Application error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()