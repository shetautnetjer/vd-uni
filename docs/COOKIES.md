# Cookies Export

Use the helper to export cookies from a browser into Netscape format files used by `yt-dlp`.

## Examples

```bash
./scripts/export_cookies --browser chrome --domain youtube.com
./scripts/export_cookies --browser brave --domain x.com
./scripts/export_cookies --browser firefox --domain pornhub.com
```

Outputs go to `config/cookies/<domain>.txt` by default.

## Browsers
- `chrome`
- `chromium`
- `brave`
- `firefox`

## Notes
- Close the browser before exporting if cookies are locked.
- Some systems require the browser keyring to be unlocked.
