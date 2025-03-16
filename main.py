"""Main entry point for the Legit Wallet Checker."""

import logging
import sys
from pathlib import Path

import torch
from web3 import Web3

from src.config import get_config, verify_cuda
from src.telegram_notifier import get_notifier
from src.wallet_manager import WalletManager, WordList

# Configure minimal logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def main():
    """Main program entry point."""
    try:
        # First verify CUDA
        verify_cuda()
        logger.warning(f"Using GPU: {torch.cuda.get_device_name(0)}")
        
        # Load configuration
        config = get_config()
        
        # Initialize Web3
        web3 = Web3()
        if not web3.isConnected():
            raise RuntimeError("Web3 connection failed")
        
        # Load word list
        word_list = WordList.from_file(config.optimization.words_file)
        logger.warning(f"Loaded {len(word_list.words)} words")
        
        # Initialize notification system
        notifier = get_notifier(config.telegram)
        notifier.notify_startup()
        
        # Start wallet checking
        wallet_manager = WalletManager(
            word_list=word_list,
            config=config.gpu,
            web3=web3
        )
        
        wallet_manager.start_processing()
        
    except KeyboardInterrupt:
        logger.warning("Shutting down...")
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    # Ensure src in path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Run main program
    main()