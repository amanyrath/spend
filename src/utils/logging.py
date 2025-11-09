"""Logging configuration for SpendSense.

This module provides structured logging setup with appropriate log levels
and formatting for both development and production environments.
"""

import logging
import sys
import os
from typing import Optional

# Default log level based on environment
DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Log format for structured logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """Set up logging configuration.
    
    Args:
        log_level: Log level (DEBUG, INFO, WARN, ERROR). If None, uses DEFAULT_LOG_LEVEL.
        
    Returns:
        Configured logger instance
    """
    level = log_level or DEFAULT_LOG_LEVEL
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger("spendsense")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"spendsense.{name}")


# Initialize default logger
logger = setup_logging()







