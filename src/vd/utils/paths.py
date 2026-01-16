from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "config"
LOGS_DIR = PROJECT_ROOT / "logs"
PACKAGES_DIR = PROJECT_ROOT / "packages"
TROUBLESHOOTING_DIR = PROJECT_ROOT / "troubleshooting"


def ensure_dirs() -> None:
    for path in (CONFIG_DIR, LOGS_DIR, PACKAGES_DIR, TROUBLESHOOTING_DIR):
        path.mkdir(parents=True, exist_ok=True)
