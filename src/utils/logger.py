import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

_logger_instances = {}

def setup_logger() -> logging.Logger:
    """Setup root logger with console and file handlers"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Console handler with color formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_dir / "wallet_stealer.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Remove existing handlers if any
    logger.handlers.clear()
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance with the specified name"""
    if name not in _logger_instances:
        logger = logging.getLogger(name)
        _logger_instances[name] = logger
    return _logger_instances[name]