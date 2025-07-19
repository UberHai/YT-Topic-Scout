"""Logging configuration for YouTube Topic-Scout."""
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str = "youtube_scout", log_level: str = "INFO") -> logging.Logger:
    """Set up structured logging with file and console output."""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    if logger.handlers:
        return logger
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter(
        '%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # File handler with rotation
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(
        log_dir / f"{name}_{timestamp}.log",
        encoding='utf-8'
    )
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)8s | %(name)s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Global logger instance
logger = setup_logger()
