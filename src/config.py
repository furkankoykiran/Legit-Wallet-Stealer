"""Configuration module for the wallet checker."""
import os
from dotenv import load_dotenv

# Load environment variables if .env exists
if os.path.exists('.env'):
    load_dotenv()

# Telegram Configuration (Optional)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
if TELEGRAM_CHAT_ID:
    try:
        TELEGRAM_CHAT_ID = int(TELEGRAM_CHAT_ID)
    except:
        TELEGRAM_CHAT_ID = None

# Ethereum Configuration
# Try local Geth first, then fallback to Infura
INFURA_API_KEY = os.getenv('INFURA_API_KEY', 'bf199b5244e34743bf3832e4659c10b2')  # Public key for demo
GETH_ENDPOINT = os.getenv('GETH_ENDPOINT') or f'https://mainnet.infura.io/v3/{INFURA_API_KEY}'

# Application Configuration
MNEMONIC_WORD_COUNT = int(os.getenv('MNEMONIC_WORD_COUNT', 12))

# Load system configuration
def load_system_config():
    """Load system configuration values."""
    return {
        'telegram_enabled': bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID),
        'geth_endpoint': GETH_ENDPOINT,
        'batch_size': int(os.getenv('BATCH_SIZE', '1000')),
        'mnemonic_word_count': MNEMONIC_WORD_COUNT
    }