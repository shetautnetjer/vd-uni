from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from vd.core.config import COOKIES_DIR, COOKIES_FILE, Settings
from vd.utils.url import extract_domain, validate_url
from vd.utils.privacy import redact_text


def _cookies_for_url(url: str, settings: Settings) -> Path | None:
    if not settings.use_cookies:
        return None
    if settings.per_site_cookies:
        domain = extract_domain(url)
        if domain:
            candidate = COOKIES_DIR / f'{domain}.txt'
            if candidate.is_file() and candidate.stat().st_size > 0:
                return candidate
    if COOKIES_FILE.is_file() and COOKIES_FILE.stat().st_size > 0:
        return COOKIES_FILE
    return None


def build_args(url: str, settings: Settings, *, list_formats: bool = False) -> list[str]:
    url = validate_url(url)
    args = [
        sys.executable, '-m', 'yt_dlp', '--ignore-config', '--newline',
        '-f', settings.quality,
        '-P', str(settings.output_dir),
        '-o', '%(title).180B [%(id)s].%(ext)s',
        '--trim-filenames', '230', '--no-overwrites', '--continue',
        '--retries', str(settings.retries), '--fragment-retries', str(settings.retries),
        '--socket-timeout', str(settings.socket_timeout),
        '--abort-on-unavailable-fragments',
    ]
    cookies_file = _cookies_for_url(url, settings)
    if cookies_file:
        args += ['--cookies', str(cookies_file)]
    if settings.live_from_start:
        args.append('--live-from-start')
    if settings.concurrent_fragments > 1:
        args += ['--concurrent-fragments', str(settings.concurrent_fragments)]
    if settings.remux_video:
        args += ['--remux-video', settings.remux_video, '--keep-video']
    if settings.recode_video:
        args += ['--recode-video', settings.recode_video, '--keep-video']
    if list_formats:
        args += ['--list-formats', '--skip-download']
    # Never turn on --allow-unplayable-formats merely because this is HLS/DASH.
    return args + ['--', url]


def run_download(url: str, settings: Settings, *, list_formats: bool = False) -> int:
    try:
        with subprocess.Popen(build_args(url, settings, list_formats=list_formats),
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, encoding='utf-8', errors='replace', bufsize=1) as proc:
            assert proc.stdout is not None
            for line in proc.stdout:
                print(redact_text(line), end='', flush=True)
            return proc.wait()
    except (OSError, ValueError) as exc:
        logging.getLogger('vd').error('Cannot start download: %s', exc)
        return 2


def run_downloads(urls: list[str], settings: Settings) -> int:
    # Keep order and signed query strings; do not merge distinct signed resources.
    unique = list(dict.fromkeys(url.strip() for url in urls if url.strip()))
    if not unique:
        return 2
    result = 0
    for index, url in enumerate(unique, 1):
        logging.getLogger('vd').info('Download %s/%s', index, len(unique))
        rc = run_download(url, settings)
        if rc != 0:
            result = rc
    return result
