"""System service module for handling system-level operations."""
import os
import platform
import subprocess
import shutil
import torch
import psutil
from colorama import Fore, Style

class SystemService:
    """Handles system-level operations like Geth installation and hardware detection."""

    @staticmethod
    def check_gpu_availability():
        """Check if GPU is available and return device type."""
        try:
            if torch.cuda.is_available():
                # Force CUDA device index 0 for GTX 1650
                torch.cuda.set_device(0)
                device = torch.device("cuda:0")
                gpu_name = torch.cuda.get_device_name(0)
                print(f"{Fore.GREEN}GPU detected: {gpu_name}{Style.RESET_ALL}")
                # Test GPU with a small tensor operation
                test_tensor = torch.rand(1000, 1000, device=device)
                test_tensor.sum()  # Force computation
                return device
        except Exception as e:
            print(f"{Fore.YELLOW}GPU error: {e}, falling back to CPU{Style.RESET_ALL}")
        
        print(f"{Fore.YELLOW}Using CPU mode{Style.RESET_ALL}")
        return torch.device("cpu")

    @staticmethod
    def get_optimal_worker_count():
        """Get optimal worker count based on system resources."""
        try:
            if torch.cuda.is_available():
                gpu_mem = torch.cuda.get_device_properties(0).total_memory
                # Adjust worker count based on GPU memory (in bytes)
                return max(min(gpu_mem // (1024**3) * 2, 16), 4)  # 2 workers per GB, min 4, max 16
        except:
            pass
        
        cpu_count = psutil.cpu_count(logical=False) or psutil.cpu_count()
        return max(cpu_count * 2, 4)  # At least 4 workers

    @staticmethod
    def ensure_geth_running():
        """Ensure Geth is installed and running."""
        # First check if Geth is already running
        if SystemService._check_geth_running():
            print(f"{Fore.GREEN}Geth is already running{Style.RESET_ALL}")
            return True

        system = platform.system().lower()
        
        if system == "linux":
            return SystemService._handle_linux_geth()
        elif system == "darwin":  # macOS
            print(f"{Fore.YELLOW}MacOS detected. Please install and run Geth manually.{Style.RESET_ALL}")
            return False
        elif system == "windows":
            print(f"{Fore.YELLOW}Windows detected. Please ensure Geth is running.{Style.RESET_ALL}")
            return False
        
        return False

    @staticmethod
    def _handle_linux_geth():
        """Handle Geth installation and running on Linux."""
        try:
            # Check if Geth is installed
            if not shutil.which("geth"):
                print(f"{Fore.YELLOW}Geth not found. Installing...{Style.RESET_ALL}")
                
                # Detect package manager
                if shutil.which("apt"):
                    # Ubuntu/Debian
                    subprocess.run([
                        "sudo", "add-apt-repository", "-y", "ppa:ethereum/ethereum"
                    ], check=True)
                    subprocess.run(["sudo", "apt", "update"], check=True)
                    subprocess.run(["sudo", "apt", "install", "-y", "geth"], check=True)
                elif shutil.which("yum"):
                    # CentOS/RHEL
                    subprocess.run([
                        "sudo", "yum", "install", "-y", "epel-release"
                    ], check=True)
                    subprocess.run([
                        "sudo", "yum", "install", "-y", "ethereum"
                    ], check=True)
                else:
                    print(f"{Fore.RED}Unsupported Linux distribution{Style.RESET_ALL}")
                    return False

            # Check if Geth is running
            geth_running = SystemService._check_geth_running()
            if not geth_running:
                print(f"{Fore.YELLOW}Starting Geth...{Style.RESET_ALL}")
                # Start Geth in background
                subprocess.Popen([
                    "geth", "--http", "--http.port", "8545",
                    "--cache", "2048", "--maxpeers", "30"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Wait for Geth to start
                import time
                retries = 30
                while retries > 0 and not SystemService._check_geth_running():
                    time.sleep(1)
                    retries -= 1
                
                if retries == 0:
                    print(f"{Fore.RED}Failed to start Geth{Style.RESET_ALL}")
                    return False
                
                print(f"{Fore.GREEN}Geth started successfully{Style.RESET_ALL}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}Error installing/running Geth: {e}{Style.RESET_ALL}")
            return False
        except Exception as e:
            print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
            return False

    @staticmethod
    def _check_geth_running():
        """Check if Geth is running by testing the RPC endpoint."""
        try:
            import requests
            response = requests.post(
                "http://127.0.0.1:8545",
                json={"jsonrpc": "2.0", "method": "eth_syncing", "params": [], "id": 1},
                timeout=2
            )
            return response.status_code == 200
        except:
            return False