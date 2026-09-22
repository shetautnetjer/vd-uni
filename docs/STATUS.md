# Status: 0.2.0

Downloader reliability, local FFmpeg/VLC conversion, content probing, dependency
and format diagnostics, GUI settings/threading fixes, expanded Chrome capture,
and an isolated regression suite are implemented. See `docs/VALIDATION.md` for
measured coverage and explicit limitations. Conversion is CLI-only; the existing
GUI remains a downloader. `sites.json` remains informational, not an access policy.
