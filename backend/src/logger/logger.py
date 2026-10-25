import logging
from logging.config import dictConfig
from pathlib import Path

Path("logs").mkdir(parents=True, exist_ok=True)

# Define logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "logs/app.log",
            "formatter": "default",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

# Apply logging configuration
dictConfig(LOGGING_CONFIG)

# Create a logger instance
logger = logging.getLogger("app_logger")