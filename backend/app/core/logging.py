"""Logging configuration."""
import logging
import sys

from app.core.config import settings


def setup_logging():
    """Configure application logging."""
    log_level = logging.DEBUG if settings.ENV == "development" else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

