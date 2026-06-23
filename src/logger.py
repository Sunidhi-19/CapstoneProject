"""Logging configuration for the application."""

import logging
from src.config import Config


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(Config.LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(Config.LOG_LEVEL)

    return logger
