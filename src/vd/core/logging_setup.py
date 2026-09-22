from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from vd.utils.paths import LOGS_DIR, ensure_dirs
from vd.utils.privacy import PrivateFormatter


def configure_logging() -> logging.Logger:
    ensure_dirs()
    logger = logging.getLogger("vd")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        LOGS_DIR / "vd.log",
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    fmt = PrivateFormatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler.setFormatter(fmt)

    console = logging.StreamHandler()
    console.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console)
    return logger
