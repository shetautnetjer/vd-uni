from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from vd.utils.paths import CONFIG_DIR

DOWNLOAD_CONTAINERS = ('avi', 'flv', 'gif', 'mkv', 'mov', 'mp4', 'webm')


@dataclass
class Settings:
    output_dir: Path
    quality: str
    use_cookies: bool
    live_from_start: bool
    per_site_cookies: bool
    concurrent_fragments: int = 4
    retries: int = 10
    socket_timeout: int = 30
    remux_video: str | None = None
    recode_video: str | None = None

    def __post_init__(self) -> None:
        self.output_dir = Path(self.output_dir).expanduser()
        if not isinstance(self.quality, str) or not self.quality.strip():
            raise ValueError('quality must be a non-empty yt-dlp format selector')
        for name in ('use_cookies', 'live_from_start', 'per_site_cookies'):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f'{name} must be a JSON boolean (true or false)')
        for name, lower, upper in (('concurrent_fragments', 1, 32), ('retries', 0, 100), ('socket_timeout', 1, 3600)):
            value = getattr(self, name)
            if type(value) is not int or not lower <= value <= upper:
                raise ValueError(f'{name} must be an integer between {lower} and {upper}')
        for name in ('remux_video', 'recode_video'):
            value = getattr(self, name)
            if value is not None and value not in DOWNLOAD_CONTAINERS:
                raise ValueError(f'{name} must be one of {", ".join(DOWNLOAD_CONTAINERS)} or null')
        if self.remux_video and self.recode_video:
            raise ValueError('Choose remux_video OR recode_video, not both')


DEFAULT_SETTINGS = Settings(
    output_dir=Path('./downloads'),
    quality='bestvideo+bestaudio/best',
    use_cookies=True,
    live_from_start=False,
    per_site_cookies=True,
)
CONFIG_FILE = CONFIG_DIR / 'settings.json'
SITES_FILE = CONFIG_DIR / 'sites.json'
COOKIES_FILE = CONFIG_DIR / 'cookies.txt'
COOKIES_DIR = CONFIG_DIR / 'cookies'


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise ValueError(f'Invalid JSON in {path.name} at line {exc.lineno}') from exc
    if not isinstance(data, dict):
        raise ValueError(f'{path.name} must contain a JSON object')
    return data


def load_settings() -> Settings:
    data = _load_json(CONFIG_FILE)
    values = asdict(DEFAULT_SETTINGS)
    values.update({key: data[key] for key in values if key in data})
    if not isinstance(values['output_dir'], (str, Path)) or not str(values['output_dir']).strip():
        raise ValueError('output_dir must be a non-empty path')
    return Settings(**values)


def ensure_config_files() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        values = asdict(DEFAULT_SETTINGS)
        values['output_dir'] = str(values['output_dir'])
        CONFIG_FILE.write_text(json.dumps(values, indent=2) + '\n', encoding='utf-8')
    if not SITES_FILE.exists():
        SITES_FILE.write_text(json.dumps({'youtube': {'enabled': True, 'notes': 'Default adapter uses yt-dlp'}}, indent=2), encoding='utf-8')
    if not COOKIES_FILE.exists():
        COOKIES_FILE.touch(mode=0o600)
    COOKIES_DIR.mkdir(parents=True, exist_ok=True)
