# Legit Wallet Checker

A GPU-accelerated Ethereum wallet balance checker that generates and validates wallet addresses using mnemonic phrases.

## Features

- 🚀 GPU acceleration for rapid wallet generation and validation
- 🔄 Multi-processing support for optimal performance
- 🤖 Telegram notifications for discovered wallets
- ☁️ Google Colab support with GPU acceleration
- 📦 Modern Python packaging with Poetry
- 🏗️ Clean, modular OOP architecture

## Installation

### Local Installation

1. Ensure you have Python 3.12+ and Poetry installed:
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

2. Clone the repository:
```bash
git clone https://github.com/furkankoykiran/Legit-Wallet-Stealer
cd Legit-Wallet-Stealer
```

3. Install dependencies:
```bash
poetry install
```

4. Configure environment variables:
```bash
# Create .env file
cat > .env << EOL
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
GETH_PATH=/path/to/geth  # Optional
EOL
```

### Google Colab Installation

For GPU acceleration without local setup, you can run the project directly in Google Colab:

1. Open the [Wallet Checker Notebook](colab/wallet_checker.ipynb) in Google Colab
2. Configure your Telegram bot token and chat ID in the notebook
3. Run all cells to start the wallet checker

## Configuration

### Telegram Bot Setup

1. Create a new bot with [@BotFather](https://t.me/BotFather)
2. Copy the provided bot token
3. Add the bot to a group and get the chat ID
4. Set these values in your environment variables or Colab notebook

### Performance Tuning

The wallet checker can be configured via environment variables:

- `BATCH_SIZE`: Number of wallets to check in parallel (default: 1024)
- `NUM_WORKERS`: Number of worker processes (default: 3)
- `DEVICE`: Computation device - "cuda" or "cpu" (default: "cuda")

## Project Structure

```
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── wallet_manager.py  # GPU-accelerated wallet operations
│   └── telegram_notifier.py # Notification handling
├── colab/
│   └── wallet_checker.ipynb # Google Colab integration
├── main.py                # Application entry point
├── pyproject.toml         # Project dependencies
└── README.md             # Documentation
```

## Support Development

If you find this project useful, consider buying me a coffee:

<a href="https://www.buymeacoffee.com/furkankoykiran">
    <img src="https://bmc-cdn.nyc3.digitaloceanspaces.com/BMC-button-images/custom_images/orange_img.png" alt="Buy Me A Coffee">
</a>

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
