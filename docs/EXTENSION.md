# Chrome Extension (Dev Mode)

This repo includes a small Chrome extension that captures `.ts` and `.m3u8` URLs
from browser network traffic so you can batch-download them with VD-uni.

## Load the extension (Dev Mode)

1. Open Chrome and go to `chrome://extensions`.
2. Enable **Developer mode** (top right).
3. Click **Load unpacked** and select `extensions/vd-uni-chrome`.
4. Pin the extension to the toolbar for easy access.

## Capture URLs

1. Toggle **Capture .ts/.m3u8 URLs** on in the popup.
2. Play the media in the tab you want to download from.
3. Open the extension popup to view captured URLs.
4. Use **Download urls.txt** or **Copy** to export.

## Download in VD-uni

```bash
./scripts/vd download --file urls.txt
```

This works for direct `.ts` segment URLs or `.m3u8` playlists.

## Notes

- The extension only observes traffic; it does not bypass DRM or paywalls.
- Use cookie export when a site requires authentication:

```bash
./scripts/vd cookies --browser chrome --domain example.com
```
