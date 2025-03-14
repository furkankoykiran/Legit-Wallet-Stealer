# Ethereum Wallet Checker

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GPU Support](https://img.shields.io/badge/GPU-CUDA-green.svg)](https://developer.nvidia.com/cuda-toolkit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/furkankoykiran/Legit-Wallet-Stealer/blob/main/wallet_checker.ipynb)

> An educational project demonstrating high-performance blockchain interactions with GPU acceleration

This project showcases various blockchain concepts including mnemonic phrase generation, wallet creation, and balance checking. It features GPU acceleration, automatic hardware optimization, and cloud execution support.

⚠️ **Educational Purpose Only:** This project is meant for learning about blockchain technology and should not be used for any malicious purposes.

## 🚀 Features

### Hardware Optimization
- 🎮 GPU acceleration for mnemonic generation
- 💻 Automatic CPU core detection and optimization
- ⚡ Dynamic worker count based on hardware capabilities

### Performance
- 🔄 Multi-threaded wallet processing
- 📦 Efficient batch operations
- 🚄 GPU-accelerated computations
- 🔧 Automatic resource balancing

### System Integration
- 🐧 Automatic Geth setup on Linux
- ☁️ Cloud provider support (Infura/Alchemy)
- 🤖 Optional Telegram notifications
- 🎨 Color-coded terminal UI

### Development
- 📦 Poetry dependency management
- 🧪 Comprehensive error handling
- 📚 Google Colab support
- 🏗️ Modular architecture

## 🎯 Quick Start

### Local Installation

1. Clone and setup:
```bash
git clone https://github.com/furkankoykiran/Legit-Wallet-Stealer
cd Legit-Wallet-Stealer
poetry install
```

2. Configure (optional):
```bash
cp .env.example .env
# Edit .env with your Telegram credentials if desired
```

3. Run:
```bash
poetry run python main.py
```

### Google Colab

Simply open the [notebook](https://colab.research.google.com/github/furkankoykiran/Legit-Wallet-Stealer/blob/main/wallet_checker.ipynb) and run all cells!

## 💻 Requirements

- Python 3.12+
- Poetry package manager
- Optional:
  * NVIDIA GPU with CUDA support
  * Geth (auto-installed on Linux)
  * Telegram credentials

## 🔧 Configuration

The `.env` file supports these settings:

```env
# Required for Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Ethereum Connection (Optional, defaults to Infura)
GETH_ENDPOINT=http://127.0.0.1:8545

# Optional Settings
MNEMONIC_WORD_COUNT=12  # Default: 12
```

## 📊 Performance

### GPU Mode
- CUDA-accelerated mnemonic generation
- Larger batch processing
- Increased worker threads
- Optimized memory usage

### CPU Mode
- Multi-core optimization
- Efficient thread distribution
- Memory-aware batch sizing
- Dynamic load balancing

## 🏗️ Project Structure

```
├── src/
│   ├── config.py           # Configuration management
│   ├── ethereum_service.py # Ethereum interaction logic
│   ├── system_service.py   # System and hardware management
│   ├── telegram_service.py # Notification service
│   └── wallet_checker.py   # Core wallet checking logic
├── main.py                 # Application entry point
├── wallet_checker.ipynb    # Google Colab notebook
├── words.txt               # Mnemonic word list (auto-downloaded)
├── .env.example            # Configuration template
└── pyproject.toml          # Poetry configuration
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⭐ Support

If you find this project helpful, please consider giving it a star on GitHub! You can also support development via:

<a href="https://www.buymeacoffee.com/furkankoykiran">
  <img src="https://bmc-cdn.nyc3.digitaloceanspaces.com/BMC-button-images/custom_images/orange_img.png" alt="Buy Me A Coffee">
</a>

## 👤 Author

**Furkan Köykıran**

- GitHub: [@furkankoykiran](https://github.com/furkankoykiran)
- LinkedIn: [Furkan Köykıran](https://www.linkedin.com/in/furkankoykiran)

## 📜 Citation

If you use this project in your research or work, please cite it as:

```bibtex
@software{ethereum_wallet_checker,
  author = {Köykıran, Furkan},
  title = {Ethereum Wallet Checker},
  year = {2024},
  url = {https://github.com/furkankoykiran/Legit-Wallet-Stealer}
}
