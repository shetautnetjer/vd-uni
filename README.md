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

### 4b) GUI

```bash
./scripts/vd-gui
```

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
