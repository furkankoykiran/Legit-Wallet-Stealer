# Legit-Wallet-Stealer

A high-performance, GPU-accelerated cryptocurrency wallet checker that monitors multiple blockchains in parallel. This project utilizes CUDA acceleration for maximum efficiency in generating and checking wallet addresses across different networks.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/furkankoykiran/Legit-Wallet-Stealer/blob/main/wallet_stealer.ipynb)

## Features

- 🚀 GPU-accelerated wallet generation using CUDA (CuPy)
- 💠 Multi-chain support (ETH, BSC, POLYGON, AVALANCHE)
- 💰 Automatic token discovery and value calculation
- 📊 Real-time price tracking via exchange APIs
- 🔔 Instant Telegram notifications for valuable wallets
- 🎯 Smart memory management and batch processing
- 📈 Automatic scaling based on available GPU resources
- 🔄 Continuous operation with error recovery
- 🛡️ Robust error handling and logging

## Quick Start (Google Colab)

1. Click the "Open in Colab" button above
2. Enable GPU runtime: Runtime > Change runtime type > GPU
3. Run all cells in order
4. Enter your Telegram credentials when prompted

## Requirements

- Python 3.8+
- CUDA-compatible GPU (for GPU acceleration)
- Telegram Bot Token and Chat ID
- Internet connection

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/furkankoykiran/Legit-Wallet-Stealer.git
cd Legit-Wallet-Stealer
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables in `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
ENABLE_GPU=true
BATCH_SIZE=5000
NUM_GPU_STREAMS=4
CHECK_INTERVAL=60
MIN_TOKEN_VALUE_USD=10.0
```

### Google Colab Detailed Setup

1. Click the "Open in Colab" button at the top of this README
2. Enable GPU runtime:
   - Click Runtime in the menu
   - Select "Change runtime type"
   - Choose "GPU" from the hardware accelerator dropdown
   - Click "Save"
3. Run all cells in order:
   - Each cell will show a checkmark when completed
   - The system will verify GPU availability
   - You'll be prompted for Telegram credentials
4. Monitor the execution:
   - Check GPU utilization in the provided stats
   - Watch for Telegram notifications
   - View logs in the output

## Architecture

The project follows a modular OOP design with the following components:

### Core Components
- `WalletManager`: Handles wallet generation and processing using GPU acceleration
- `BlockchainManager`: Manages blockchain connections and token operations
- `TelegramService`: Handles notification delivery

### Utilities
- `GPUContext`: Manages GPU resources and memory
- `Logger`: Provides structured logging across components

### Performance Optimizations

1. **GPU Acceleration**
   - Batch processing of wallet generation
   - Parallel memory operations
   - Efficient memory management with CuPy
   - Automatic batch size optimization

2. **Network Optimization**
   - Asynchronous blockchain queries
   - Connection pooling
   - Request batching
   - Smart caching for token prices

3. **Resource Management**
   - Automatic GPU memory cleanup
   - Connection pooling for Web3
   - Efficient error handling and recovery

## Usage

### Running Locally

```bash
python main.py
```

### Running on Google Colab

Simply click the "Open in Colab" button at the top of this README and follow the Quick Start instructions.

## Monitoring

- Check the `logs` directory for detailed operation logs
- Monitor Telegram for valuable wallet notifications
- Use `nvidia-smi` to monitor GPU usage

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## Disclaimer

This project is for educational purposes only. Always respect privacy and follow applicable laws and regulations.

## License

MIT License - see LICENSE file for details
