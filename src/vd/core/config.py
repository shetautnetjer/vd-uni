from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vd.utils.paths import CONFIG_DIR


@dataclass
class Settings:
    output_dir: Path
    quality: str
    use_cookies: bool
    live_from_start: bool
    per_site_cookies: bool


DEFAULT_SETTINGS = Settings(
    output_dir=Path("./downloads"),
    quality="bestvideo+bestaudio/best",
    use_cookies=True,
    live_from_start=False,
    per_site_cookies=True,
)


CONFIG_FILE = CONFIG_DIR / "settings.json"
SITES_FILE = CONFIG_DIR / "sites.json"
COOKIES_FILE = CONFIG_DIR / "cookies.txt"
COOKIES_DIR = CONFIG_DIR / "cookies"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_settings() -> Settings:
    data = _load_json(CONFIG_FILE)
    output_dir = Path(data.get("output_dir", DEFAULT_SETTINGS.output_dir))
    return Settings(
        output_dir=output_dir,
        quality=data.get("quality", DEFAULT_SETTINGS.quality),
        use_cookies=bool(data.get("use_cookies", DEFAULT_SETTINGS.use_cookies)),
        live_from_start=bool(data.get("live_from_start", DEFAULT_SETTINGS.live_from_start)),
        per_site_cookies=bool(data.get("per_site_cookies", DEFAULT_SETTINGS.per_site_cookies)),
    )


def ensure_config_files() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(
            json.dumps(
                {
                    "output_dir": str(DEFAULT_SETTINGS.output_dir),
                    "quality": DEFAULT_SETTINGS.quality,
                    "use_cookies": DEFAULT_SETTINGS.use_cookies,
                    "live_from_start": DEFAULT_SETTINGS.live_from_start,
                    "per_site_cookies": DEFAULT_SETTINGS.per_site_cookies,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    if not SITES_FILE.exists():
        SITES_FILE.write_text(
            json.dumps(
                {
                    "youtube": {
                        "enabled": True,
                        "notes": "Default adapter uses yt-dlp",
                    }
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    if not COOKIES_FILE.exists():
        COOKIES_FILE.write_text("", encoding="utf-8")
    COOKIES_DIR.mkdir(parents=True, exist_ok=True)
