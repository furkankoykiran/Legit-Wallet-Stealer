"""Optimized configuration management."""

import os
from dataclasses import dataclass
from typing import Optional

import torch
import torch.backends.cuda
import torch.backends.cudnn

def verify_cuda() -> None:
    """Initialize and verify CUDA availability."""
    # Force PyTorch to use CUDA
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
    
    # Check CUDA availability
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required")
    
    # Initialize CUDA
    device = torch.device("cuda")
    torch.cuda.init()
    _ = torch.zeros(1).to(device)  # Force CUDA initialization
    
    # Enable optimizations
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.enabled = True
    torch.backends.cudnn.benchmark = True
    torch.backends.cudnn.allow_tf32 = True
    torch.backends.cuda.enable_mem_efficient_sdp = True
    
    # Set optimal memory allocation
    torch.cuda.set_device(0)
    torch.cuda.empty_cache()
    torch.cuda.memory.set_per_process_memory_fraction(0.95)

@dataclass(frozen=True)
class TelegramConfig:
    """Telegram configuration."""
    token: str
    chat_id: int
    
    @classmethod
    def from_env(cls) -> 'TelegramConfig':
        """Create from environment variables."""
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not token or not chat_id:
            raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
            
        return cls(token=token, chat_id=int(chat_id))

@dataclass(frozen=True)
class GPUConfig:
    """Optimized GPU configuration."""
    
    @property
    def batch_size(self) -> int:
        """Calculate optimal batch size based on GPU memory."""
        gpu_mem = torch.cuda.get_device_properties(0).total_memory
        return min(int((gpu_mem * 0.8) // (12 * 4)), 32768)
    
    @property
    def num_workers(self) -> int:
        """Calculate optimal number of workers based on GPU."""
        gpu_count = torch.cuda.device_count()
        cpu_count = os.cpu_count() or 1
        return min(gpu_count * 4, cpu_count, 16)

    @property
    def device(self) -> torch.device:
        """Get CUDA device."""
        return torch.device("cuda")

@dataclass(frozen=True)
class OptimizationConfig:
    """Performance optimization settings."""
    disable_gc: bool = True
    torch_num_threads: int = 4
    words_file: str = "words.txt"  # Default words file location

@dataclass(frozen=True)
class Config:
    """Main configuration."""
    telegram: TelegramConfig
    gpu: GPUConfig = GPUConfig()
    optimization: OptimizationConfig = OptimizationConfig()
    
    @classmethod
    def load(cls) -> 'Config':
        """Load configuration."""
        # Initialize CUDA first
        verify_cuda()
        
        return cls(
            telegram=TelegramConfig.from_env(),
            gpu=GPUConfig(),
            optimization=OptimizationConfig()
        )

    def apply_system_optimizations(self):
        """Apply system-wide optimizations."""
        if self.optimization.disable_gc:
            import gc
            gc.disable()
            
        if self.optimization.torch_num_threads:
            torch.set_num_threads(self.optimization.torch_num_threads)

# Global singleton
_config: Optional[Config] = None

def get_config() -> Config:
    """Get optimized global configuration."""
    global _config
    if _config is None:
        _config = Config.load()
        _config.apply_system_optimizations()
    return _config