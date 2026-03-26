"""Structured logging helpers for GI Scribe."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(log_dir: Path = Path("local_storage") / "logs") -> None:
    """Initialize root logger with console + file handlers."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    from logging.handlers import RotatingFileHandler
    
    # 10MB per file, max 5 backup files
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
    )
    
    stream_handler = logging.StreamHandler()
    
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Avoid adding handlers multiple times in hot-reload
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING) # Reduce noise
