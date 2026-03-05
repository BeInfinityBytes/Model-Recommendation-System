# src/shared/utils/logger.py
from __future__ import annotations
import structlog
import logging
import sys
from typing import Any, Dict

from ..config.settings import settings

def configure_logging() -> None:
    """Configure structlog + stdlib logging to output structured logs.

    This function is idempotent; call early in your application startup
    (e.g., in FastAPI startup event).
    """
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    pre_chain = [
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a structlog logger bound to module name."""
    configure_logging()
    return structlog.get_logger(name)
