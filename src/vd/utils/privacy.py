"""Conservative redaction for human-readable diagnostics, never execution input."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from urllib.parse import urlsplit

from vd.utils.paths import CONFIG_DIR, LOGS_DIR, PROJECT_ROOT

_URL = re.compile(r'(?:https?|ftps?|rtmps?|rtsp)://[^\s<>\"\']+', re.IGNORECASE)


def redact_text(text: str, *, roots: list[str] | None = None) -> str:
    def public_origin(match: re.Match[str]) -> str:
        try:
            parsed = urlsplit(match.group())
            host = parsed.hostname
            if not host:
                return '<redacted-url>'
            # Keep only the origin. Tokens may be in paths as well as queries.
            return f'{parsed.scheme}://{host}/<redacted>'
        except ValueError:
            return '<redacted-url>'
    result = _URL.sub(public_origin, str(text))
    private_roots = roots if roots is not None else [str(PROJECT_ROOT), str(CONFIG_DIR), str(LOGS_DIR), str(Path.home())]
    for root in sorted(set(private_roots), key=len, reverse=True):
        if len(root) > 1:
            result = result.replace(root, '<local>')
    return result


class PrivateFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return redact_text(super().format(record))
