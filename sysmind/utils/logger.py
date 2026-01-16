"""
SYSMIND Logger Module

Centralized logging infrastructure for the application.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for terminal output."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def __init__(self, fmt: str, use_color: bool = True):
        super().__init__(fmt)
        self.use_color = use_color
    
    def format(self, record: logging.LogRecord) -> str:
        if self.use_color:
            color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_dir: Optional[Path] = None,
    use_color: bool = True,
    log_to_file: bool = True
) -> logging.Logger:
    """
    Configure logging for SYSMIND.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        use_color: Whether to use colored output in console
        log_to_file: Whether to also log to a file
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('sysmind')
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler with optional colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_fmt = "%(levelname)s: %(message)s"
    console_handler.setFormatter(ColoredFormatter(console_fmt, use_color=use_color))
    logger.addHandler(console_handler)
    
    # File handler
    if log_to_file and log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"sysmind_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        file_handler.setFormatter(logging.Formatter(file_fmt))
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = 'sysmind') -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
