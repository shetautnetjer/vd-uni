# Config

## cookies

- Global cookies: `config/cookies.txt`
- Per-site cookies: `config/cookies/<domain>.txt`
  - Examples:
    - `config/cookies/youtube.com.txt`
    - `config/cookies/x.com.txt`
    - `config/cookies/pornhub.com.txt`
- If `per_site_cookies` is true, the downloader checks for a per-site file first, then falls back to `config/cookies.txt`.

## quality
- Default: highest
- Fallbacks: list in priority order

## sites
- Per-site settings in `config/sites.json`

