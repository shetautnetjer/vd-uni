# VD-uni

Linux-first video downloader and local media converter, with an optional Chrome
URL-capture extension. yt-dlp handles supported websites and direct streams;
FFmpeg handles broad format conversion; VLC is an optional second backend.

## Install and check

Python 3.10+ and the **FFmpeg and ffprobe executables** are required for the full
workflow. VLC is optional. The GUI additionally needs your OS's Tkinter package.

```bash
./scripts/install.sh
./scripts/vd doctor
./scripts/vd doctor --json --redact
```

The installer only creates a project `.venv` and installs Python dependencies. It
never installs system packages or modifies your browser. Full YouTube support
also needs a supported JavaScript runtime and yt-dlp-ejs (included through
`yt-dlp[default]`); Deno is the upstream-recommended, automatically detected choice.
See the upstream [EJS guide](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

## Download videos or streams

```bash
./scripts/vd download "https://example.com/video.mp4"
./scripts/vd download --file urls.txt --fragments 8
./scripts/vd download "https://example.com/stream.m3u8" --remux mkv
./scripts/vd formats "https://example.com/video"
```

Highest-quality selection remains `bestvideo+bestaudio/best`. The downloader
recognizes sites and media through yt-dlp rather than a fixed extension list.
Exact duplicate URLs are removed from batches. Downloads resume, use bounded
retries, and fail when stream fragments are missing instead of silently skipping
them. Names include media IDs, and existing files are not overwritten.

`--remux` changes the container without re-encoding when compatible; `--recode`
asks yt-dlp to convert to a container. Both retain the original download. yt-dlp
may skip recoding when the extension already matches; to force specific codecs,
use the local `convert --mode transcode` command below.

Other options: `-P/--output-dir`, `-f/--format`, `--retries`, and `--no-cookies`.
`--fragments` accepts 1–32. More concurrency is not always faster and can trigger
site rate limits. Batch files support comments and UTF-8 BOMs.

## Convert local files

```bash
# Inspects actual content, even if the input extension is unfamiliar.
./scripts/vd probe "camera recording.anything"

# Try lossless stream-copy first; re-encode only if necessary.
./scripts/vd convert "input.mkv" -o "output.mp4"

# Require a lossless remux: fail rather than silently transcode.
./scripts/vd convert "input.mov" -o "output.mkv" --mode copy

# Force widely compatible H.264/AAC MP4, even if input is already MP4.
./scripts/vd convert "input.webm" -o "output.mp4" --mode transcode

# Use VLC explicitly.
./scripts/vd convert "input.avi" -o "output.mp4" --engine vlc --mode transcode

# Optional hardware encoder; requires a working GPU/driver and FFmpeg support.
./scripts/vd convert "input.mov" -o "output.mp4" --mode transcode --video-encoder h264_nvenc

./scripts/vd formats
./scripts/vd formats --full
```

Local inputs have **no extension whitelist**. Actual support depends on installed
codecs and on ffprobe being able to inspect the source. FFmpeg has tuned output
profiles for MP4, M4V, MOV, MKV, WebM, AVI, TS/MTS/M2TS, MPG/MPEG, FLV, OGV/OGG,
and WMV/ASF. Other output extensions use FFmpeg's installed defaults. The smaller
VLC adapter exposes the verified MP4/M4V and OGV/OGG paths; use FFmpeg for TS.

The default engine tries FFmpeg, then VLC if needed. ffprobe is **still required**
for VLC validation. Every output is staged and checked for video, audio-track
count, and duration before atomic publication. Copy mode also verifies the stream
codec/type inventory. Inputs are never modified. Existing destinations require
explicit `--overwrite`. `--timeout` is a total deadline, default 3,600 seconds.

This is broad compatibility, not a promise of every proprietary codec or corrupt
file. It does not bypass DRM, paywalls, or missing access rights. Compatibility
transcoding is lossy, may omit subtitles/attachments/additional video tracks, and
is not an HDR-preservation or tone-mapping pipeline. Use copy mode for strict
stream preservation, and keep originals. See [media behavior](docs/MEDIA.md).

## Chrome capture, cookies, and GUI

Load `extensions/vd-uni-chrome` unpacked in Chrome and enable capture in the popup.
It detects common video extensions, extensionless `video/*` responses, and HLS/DASH
manifests. Individual segments are opt-in; prefer manifests for complete videos.
Capture is off for new installs, persists locally, and retains the newest 500
URLs. Existing capture preferences survive upgrades. Signed URLs can contain
access tokens: do not publish URL lists. See [extension instructions](docs/EXTENSION.md).

```bash
./scripts/vd cookies --browser chrome --domain example.com
./scripts/vd-gui
```

Per-site cookies are preferred, followed by `config/cookies.txt`. Browser cookies
are only read on the explicit cookie-export command. The GUI remains a downloader;
local conversion is currently a CLI feature. See [configuration](docs/CONFIG.md).

## Tests

```bash
# Use a small, isolated environment with FFmpeg, VLC, Tk and Node.
docker build -t vd-uni:test -f tests/Dockerfile .
docker run --rm --init --network none --cpus 2 --memory 1g \
  --cap-drop ALL --security-opt no-new-privileges \
  --mount type=bind,src="$PWD",dst=/work,readonly vd-uni:test \
  timeout 120 xvfb-run -a python -m unittest discover -s tests -v
docker run --rm --init --network none \
  --mount type=bind,src="$PWD",dst=/work,readonly vd-uni:test \
  node --test tests/test_extension.cjs
```

Tests synthesize tiny videos and serve downloads only over container-local
loopback. They do not access real websites, browser profiles, or private media.
See [validation scope](docs/VALIDATION.md). GitHub Actions runs the same commands.

## Privacy

Cookie exports are atomic and owner-only on POSIX. Human-readable download logs
redact sensitive URL components. Use `doctor --json --redact` when sharing
diagnostics, and run `python3 scripts/check_public_tree.py` before publishing.
See [privacy and safe publishing](docs/SECURITY.md) for boundaries and limitations.
