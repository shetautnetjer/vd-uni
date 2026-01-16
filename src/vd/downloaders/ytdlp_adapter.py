from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from vd.core.config import COOKIES_DIR, COOKIES_FILE, Settings
from vd.utils.url import extract_domain


def _cookies_for_url(url: str, settings: Settings) -> Path | None:
    if not settings.use_cookies:
        return None

    if settings.per_site_cookies:
        domain = extract_domain(url)
        if domain:
            candidate = COOKIES_DIR / f"{domain}.txt"
            if candidate.exists() and candidate.stat().st_size > 0:
                return candidate

    if COOKIES_FILE.exists() and COOKIES_FILE.stat().st_size > 0:
        return COOKIES_FILE

    return None


def build_args(url: str, settings: Settings) -> list[str]:
    args = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--newline",
        "-f",
        settings.quality,
        "-o",
        str(Path(settings.output_dir) / "%(title)s.%(ext)s"),
    ]

    cookies_file = _cookies_for_url(url, settings)
    if cookies_file:
        args += ["--cookies", str(cookies_file)]

    if settings.live_from_start:
        args.append("--live-from-start")

    args.append(url)
    return args


def run_download(url: str, settings: Settings) -> int:
    args = build_args(url, settings)
    proc = subprocess.run(args, check=False)
    return proc.returncode
