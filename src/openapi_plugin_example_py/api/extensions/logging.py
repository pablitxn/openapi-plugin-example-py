"""Logging configuration module."""
import logging
from typing import Optional


def configure_logging(
    level: int = logging.INFO,
    format: Optional[str] = None,
    logger_name: Optional[str] = None
) -> logging.Logger:
    """Configure application logging.
    
    Args:
        level: Logging level (default: INFO)
        format: Log format string (optional)
        logger_name: Name of the logger (optional)
        
    Returns:
        Configured logger instance
    """
    if format is None:
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=level,
        format=format
    )
    
    logger = logging.getLogger(logger_name or __name__)
    return logger