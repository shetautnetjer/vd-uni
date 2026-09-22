# Chrome URL capture

Open `chrome://extensions`, enable Developer mode, and load
`extensions/vd-uni-chrome` unpacked. Pin the popup and enable **Capture video URLs**.
New installs are opt-in; existing enabled/disabled preferences are retained.

The worker observes successful HTTP(S) responses belonging to browser tabs. It
recognizes HLS `.m3u8`, DASH `.mpd`, common video extensions, and video MIME types,
including extensionless URLs. It stores only URLs locally, not cookies or complete
request/response headers. The newest 500 unique URLs are retained. Simultaneous
captures and Clear are serialized, preventing lost updates or resurrected entries.

Individual `.ts`, `.m4s`, and related segment responses require the optional
**Include individual stream segments** checkbox. A `.ts` can also be a standalone
video: this is a capture heuristic, not a conversion restriction. Prefer a manifest
or original webpage URL for a complete HLS/DASH video; an isolated fragment may lack
initialization data, other segments, or audio.

Use **Download urls.txt** or **Copy**, then run:

```bash
./scripts/vd download --file urls.txt
```

Signed query strings are preserved exactly. They can contain access tokens and
can expire; do not publish exported lists. Some sites also need an authorized
cookie file or a webpage extractor. Capturing a URL does not guarantee downloads
are allowed or technically possible. `blob:` URLs are browser-local references,
not standalone network downloads. DRM and paywalls are not bypassed.

The extension requests HTTP(S) host visibility to detect media across sites, but
capture remains off until enabled. Its classification, concurrency, persistence,
and clearing logic have automated tests. A live Chrome end-to-end permission and
popup interaction test has not been run as part of this change.
