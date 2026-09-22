from __future__ import annotations

from urllib.parse import urlsplit

NETWORK_SCHEMES = {'http', 'https', 'ftp', 'ftps', 'rtmp', 'rtmps', 'rtsp'}


def validate_url(url: str) -> str:
    value = url.strip()
    try:
        parsed = urlsplit(value)
        valid = parsed.scheme.lower() in NETWORK_SCHEMES and bool(parsed.hostname)
        _ = parsed.port  # Validate port syntax without including credentials in errors.
    except ValueError:
        valid = False
    if not valid or any(char.isspace() or ord(char) < 32 for char in value):
        raise ValueError('Expected a network video URL; use "vd convert" for local files')
    return value


def extract_domain(url: str) -> str:
    try:
        host = (urlsplit(url).hostname or '').lower()
    except ValueError:
        return ''
    return host[4:] if host.startswith('www.') else host
