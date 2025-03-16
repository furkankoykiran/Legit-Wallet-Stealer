import cupy as cp
import numpy as np
from typing import Optional, Dict
from contextlib import contextmanager
from ..utils.logger import get_logger

logger = get_logger(__name__)

class GPUContext:
    def __init__(self, device_id: int = 0):
        self.device_id = device_id
        self.device = None
        self.memory_pool = None

    def __enter__(self):
        try:
            self.device = cp.cuda.Device(self.device_id)
            self.device.use()
            
            # Enable memory pool for better memory management
            self.memory_pool = cp.cuda.MemoryPool()
            cp.cuda.set_allocator(self.memory_pool.malloc)
            
            logger.info(f"GPU initialized: {self.get_device_info()}")
            return self
            
        except Exception as e:
            logger.error(f"Failed to initialize GPU: {str(e)}")
            return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.memory_pool:
            self.memory_pool.free_all_blocks()
        cp.cuda.set_allocator(None)

    def get_device_info(self) -> Dict[str, str]:
        """Get current GPU device information"""
        return {
            "name": cp.cuda.runtime.getDeviceProperties(self.device_id)["name"].decode(),
            "compute_capability": ".".join(
                map(str, cp.cuda.runtime.getDeviceProperties(self.device_id)["computeCapability"])
            ),
            "total_memory": f"{cp.cuda.runtime.memGetInfo()[1] / (1024**3):.2f} GB",
            "free_memory": f"{cp.cuda.runtime.memGetInfo()[0] / (1024**3):.2f} GB",
        }

def check_gpu_availability() -> bool:
    """Check if CUDA GPU is available"""
    try:
        return cp.cuda.runtime.getDeviceCount() > 0
    except Exception:
        return False

def setup_gpu_context(device_id: int = 0) -> Optional[GPUContext]:
    """Setup GPU context with error handling"""
    try:
        context = GPUContext(device_id)
        if context.__enter__():
            return context
    except Exception as e:
        logger.error(f"Error setting up GPU context: {str(e)}")
    return None

@contextmanager
def gpu_array_context(shape: tuple, dtype=cp.float32):
    """Context manager for safely handling GPU arrays"""
    array = None
    try:
        array = cp.zeros(shape, dtype=dtype)
        yield array
    finally:
        if array is not None:
            array.get()  # Synchronize with host
            del array
            cp.get_default_memory_pool().free_all_blocks()

def optimize_batch_size(available_memory: int, element_size: int) -> int:
    """Calculate optimal batch size based on available GPU memory"""
    # Use 80% of available memory to be safe
    safe_memory = int(available_memory * 0.8)
    return safe_memory // element_size

def cpu_fallback(func):
    """Decorator to fallback to CPU if GPU operation fails"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"GPU operation failed, falling back to CPU: {str(e)}")
            # Convert CuPy arrays to NumPy arrays
            cpu_args = [
                arg.get() if isinstance(arg, cp.ndarray) else arg 
                for arg in args
            ]
            cpu_kwargs = {
                k: v.get() if isinstance(v, cp.ndarray) else v 
                for k, v in kwargs.items()
            }
            # Replace CuPy functions with NumPy equivalents
            return func.__name__.replace('cp.', 'np.')(*cpu_args, **cpu_kwargs)
    return wrapper

def memory_cleanup():
    """Clean up GPU memory"""
    try:
        cp.get_default_memory_pool().free_all_blocks()
        cp.cuda.runtime.deviceSynchronize()
    except Exception as e:
        logger.error(f"Error cleaning up GPU memory: {str(e)}")