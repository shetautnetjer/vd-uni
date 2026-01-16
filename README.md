# VD-uni

Modular video downloader workspace with tooling for installs, updates, troubleshooting, and error logging.

## Layout
- `src/` core code modules
- `scripts/` runnable utilities (install, update, health checks)
- `config/` configuration (cookies, sites, quality prefs)
- `logs/` runtime logs and error reports
- `troubleshooting/` known issues and fixes
- `docs/` architecture and usage
- `tests/` tests
- `packages/` downloaded or staged artifacts

## Quick Start

### 1) Install deps

```bash
python -m pip install -r requirements.txt
```

### 2) Configure

- `config/settings.json`
- `config/sites.json`
- `config/cookies.txt` (optional)
- `config/cookies/<domain>.txt` (per-site, preferred)

### 3) Export cookies (optional)

```bash
./scripts/vd cookies --browser chrome --domain youtube.com
```

### 4) Run

```bash
./scripts/vd download "https://youtube.com/live/sayebOQcWew"
```

Bulk downloads:

```bash
./scripts/vd download --file urls.txt
./scripts/vd download "https://example.com/video1" "https://example.com/video2"
```

### 4b) GUI

```bash
./scripts/vd-gui
```

### 4c) Chrome extension (dev mode)

The repo includes a small Chrome extension to capture `.ts`/`.m3u8` URLs for
batch downloads. See `docs/EXTENSION.md`.

### 5) Update tools

```bash
./scripts/vd-update
```

## Notes
- This uses `yt-dlp` under the hood.
- Cookies are only used if cookie files exist and are non-empty.
- Default quality is highest: `bestvideo+bestaudio/best`.
- Site notes and defaults live in `docs/SITES.md`.
- Cookie export guide: `docs/COOKIES.md`.
- Downloads go to the configured `output_dir` (currently `downloads/`).
