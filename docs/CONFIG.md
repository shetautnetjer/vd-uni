# Configuration

`config/settings.json` controls downloader defaults. Existing configurations remain
valid. `VD_CONFIG_DIR` and `VD_LOGS_DIR` optionally relocate configuration and logs.
Output paths are relative to the invocation's working directory unless absolute.

| Key | Default | Meaning |
| --- | --- | --- |
| output_dir | downloads | Download destination |
| quality | bestvideo+bestaudio/best | yt-dlp format selector |
| use_cookies | true | Use an existing nonempty cookie file |
| per_site_cookies | true | Prefer an exact site's cookie file |
| live_from_start | false | Ask yt-dlp for a live stream from its beginning |
| concurrent_fragments | 4 | Simultaneous fragments, integer 1–32 |
| retries | 10 | Download and fragment retries, integer 0–100 |
| socket_timeout | 30 | Network timeout seconds, integer 1–3600 |
| remux_video | null | Optional container-only conversion |
| recode_video | null | Optional yt-dlp recoding target |

`remux_video` and `recode_video` are mutually exclusive and accept `avi`, `flv`,
`gif`, `mkv`, `mov`, `mp4`, or `webm`. The CLI's `--remux` and `--recode` override
these settings. Local `convert` supports more formats; see `vd formats`.

Booleans must be JSON `true`/`false`, not strings. Invalid values fail clearly.
`--no-cookies`, `--fragments`, `--retries`, `--format`, and `--output-dir` override
settings for one invocation without rewriting the configuration file.

## Cookies

Per-site files live at `config/cookies/<domain>.txt`. Hostnames are lowercased and
leading `www.` removed; URL credentials and ports are excluded. The lookup is
exact, not automatic parent-domain matching. If no nonempty per-site file exists,
`config/cookies.txt` is the fallback. Cookie contents remain Netscape format.

Neither tests nor ordinary downloads automatically export browser cookies. Only
run `vd cookies` when you intend to read the selected browser profile. Keep cookie
files and signed URL lists out of Git; they can grant access to accounts/content.

## Tool locations

Set `VD_FFMPEG`, `VD_FFPROBE`, or `VD_VLC` to an executable path or executable name
to override discovery for local media conversion. Otherwise PATH is used, with
`cvlc` preferred over `vlc`. These overrides do not reconfigure yt-dlp's separate
FFmpeg discovery; for downloads, put FFmpeg and ffprobe on PATH.

`config/sites.json` currently records site notes; it is **not an enforced site
allowlist**. No DRM or paywall bypass is implemented.
