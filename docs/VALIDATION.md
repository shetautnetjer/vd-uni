# Validation: 2026-09-22

## Verified result

**47 Python tests and 7 Node tests passed, with no skips, in the isolated test
container.** Python tests include a real Tk GUI regression under Xvfb. Extension
tests exercise the service worker using mocked Chrome APIs, not an actual browser.

Environment observed with `vd doctor --json`:

- Python 3.12.3
- yt-dlp 2026.8.19 and yt-dlp-ejs 0.8.0
- FFmpeg / ffprobe 6.1.1-3ubuntu5
- VLC 3.0.20 Vetinari
- Ubuntu 24.04 container, non-root runtime, 2 CPUs, 1 GiB limit,
  no external networking, read-only source mount, all capabilities dropped

These are the tested versions, not claims that they are the latest upstream
releases. The test image resolves OS and Python packages at build time, so later
builds may have different versions; record `doctor --json` when comparing runs.

## Coverage

- Direct downloads of synthetic MP4, MKV, MOV, AVI, WebM, and an extensionless
  response identified by its MIME type.
- Complete HLS and DASH downloads, with video, audio and duration checked.
- Missing HLS fragments produce a failure instead of a nominally complete video.
- Download-time remux retains the original file.
- Real FFmpeg transcoding to MP4, MKV, MOV, WebM, AVI, TS, MPG, FLV, OGV, and WMV,
  followed by conversion back to MP4.
- Content probing under an arbitrary filename extension.
- Default copy-first conversion and failure of incompatible explicit copy mode.
- VLC MP4 (H.264/AAC) and OGV (Theora/Vorbis) conversion; FFmpeg-unavailable fallback
  to VLC while ffprobe remains available.
- Protection of originals, same-file and hard-link rejection, overwrite behavior,
  corrupt input, shell metacharacters in filenames, and timeout cleanup.
- An encoder returning success without producing a file is rejected.
- Strict configuration, stable highest-quality selection, argument separation,
  explicit retries, batch deduplication, URL validation, and clean CLI errors.
- GUI settings preservation and widget updates on the main thread.
- Extension file/MIME recognition, segment distinction, simultaneous captures,
  worker restart with capture disabled, bounded storage, and serialized clearing.

## Deliberately excluded or not established

No private media or actual browser cookie databases were used. No DRM, paywall, or
authentication bypass was attempted. Public-site compatibility, a live Chrome UI
end-to-end test, GPU/NVENC functionality or benchmarks, HDR/professional color
fidelity, huge or malformed-file stress tests, and exhaustive frame decoding have
not been established by this suite.

A VLC TS transcode of a one-second fixture returned a successful process status
but no video stream. Validation caught it; that output path is deliberately not
exposed by the VLC adapter. FFmpeg TS conversion passes. VLC OGV adds a Skeleton
data stream, so tests check audio/video codecs without assuming all streams are
video or audio or that their order matches FFmpeg's.

## Reproduction

Run the Docker commands in the main README. The `--init` option is important for
proper signal handling when running Xvfb inside the container. A first trial
without it stalled before GUI tests started; the bounded, init-enabled run passes.
The test fixtures and HTTP server exist only inside the container, with the HTTP
server bound to 127.0.0.1. Tests do not need external network access after building.

GitHub Actions is configured to run the same suite. A local passing result alone
is not evidence that GitHub-hosted CI has completed; check the pull request checks.

## Privacy follow-up

Ten additional tests cover owner-only cookie replacement, symlink and control-
character rejection, hostname validation before browser access, DNS-boundary
filtering, signed/malformed URL redaction, known-root redaction, redacted
subprocess output with return-code preservation, and path-free diagnostics.

Gitleaks v8.30.1 and the public-tree guard are used for publishing checks.
The tests use fixture strings only, not real account credentials.
