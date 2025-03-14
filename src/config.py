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

# Load word list
def load_word_list(filename="words.txt"):
    """Load and process the word list from file."""
    try:
        # First try local file
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                words = [word.strip() for word in f.readlines() if len(word.strip()) > 1]
        # Fallback to downloading BIP39 wordlist
        else:
            import requests
            print("Downloading BIP39 wordlist...")
            response = requests.get('https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt')
            words = [word.strip() for word in response.text.split('\n') if word.strip()]
            # Save for future use
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write('\n'.join(words))
            except:
                pass
        return words
    except Exception as e:
        raise Exception(f"Error loading word list: {str(e)}")