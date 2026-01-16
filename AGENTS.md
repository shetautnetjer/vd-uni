# AGENTS.md

Purpose: instructions for assistants working on VD-uni.

## Primary goal
Make VD-uni work reliably on Linux, with Chrome as the only available browser right now. Ensure users can download from many sites with cookies as needed.

## Environment assumptions
- OS: Linux
- Browser: Chrome only (support others if easy)
- Core downloader: yt-dlp + ffmpeg

## Preferred flows
- Cookie export uses `./scripts/vd cookies --browser chrome --domain <domain>` or `./scripts/export_cookies ...` and writes `config/cookies/<domain>.txt`.
- Downloader should prefer per-site cookies, fallback to `config/cookies.txt` (see `docs/CONFIG.md`).
- Update site-specific behaviors in `config/sites.json` and document in `docs/SITES.md`.
- When adding troubleshooting steps, update `troubleshooting/` and `docs/COOKIES.md` if relevant.

## Implementation notes
- Keep Netscape cookie file output format (see `src/vd/utils/cookie_export.py`).
- Do not hardcode absolute paths; use `vd.utils.paths`.
- Preserve default quality `bestvideo+bestaudio/best` unless user requests.

## Validation
- `./scripts/vd cookies --browser chrome --domain example.com`
- `./scripts/vd download <url>`

## Non-goals
- Bypassing DRM or paywalls; only use cookies for authenticated content the user can access.
