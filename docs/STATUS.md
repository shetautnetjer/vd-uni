# VD-uni Status

Date: 2026-01-10

## Completed
- Created modular folder structure for VD-uni.
- Implemented Python CLI (`vd`) with subcommands:
  - `download` (yt-dlp based)
  - `cookies` (browser cookie export)
  - `update` (tool updates)
  - `help` / `commands` (prints commands file)
  - `version` (+ bump major/minor/patch)
- Added `vd-update` script to update tools and bump patch version.
- Added per-site cookies support with fallback to global cookies.
- Added cookie export helper for Chrome/Chromium, Brave, Firefox.
- Installed ffmpeg for merging audio+video.
- Verified download + merge for YouTube URL (output in `downloads/`).

## Files & Directories
- `src/vd/` core code modules
- `scripts/` CLI wrappers and helpers
- `config/` settings and cookies
- `docs/` architecture, config, cookies, sites, status
- `troubleshooting/` known issues template
- `VERSION` (current app version)
- `commands` (CLI usage reference)

## Current Behavior
- Downloads saved under `downloads/` (current setting).
- Highest quality selection: `bestvideo+bestaudio/best`.
- Cookies loaded from `config/cookies/<domain>.txt`, fallback `config/cookies.txt`.
- `vd-update` runs tool update and bumps `VERSION` patch.

## Warnings / Improvements
- yt-dlp warns about missing JS runtime for YouTube extraction.
- Consider installing a JS runtime (Node or Deno) for full format support.
- Consider adding `vd doctor` for environment checks.

## Next Ideas (User Mentioned)
- Future productization as standalone software.
- Possible browser extension integration.
