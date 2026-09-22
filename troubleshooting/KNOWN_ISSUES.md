# Known Issues

- Issue: USB output path not writable from Linux container
  - Symptoms:
    - yt-dlp fails with "Permission denied" writing to `/mnt/chromeos/removable/USB Drive/videos/*.part`.
    - `touch` in the USB folder fails with permission denied.
  - Cause:
    - Removable drive shared with Linux but not writable inside the container (ChromeOS sharing or drive is read-only).
  - Fix:
    - Re-share the USB drive in ChromeOS Files app or Linux settings (Settings → Developers → Linux → Manage shared folders).
    - Verify write by creating a file from Linux.
    - If needed, download to `downloads/` and move via ChromeOS Files app.
  - Notes:
    - 9p mount at `/mnt/chromeos` can show rw but still deny writes to removable media.

## Media compatibility and dependencies (0.2.0)

Run `./scripts/vd doctor` first. FFmpeg and ffprobe must be executables, not merely
Python packages. VLC is optional and should run as a normal user, not root.
`ffprobe` remains required when VLC is selected. The tested VLC TS transcode path
was unreliable for a short clip and is not exposed; use FFmpeg for TS output.

For incompatible containers, `--mode copy` intentionally fails. Use an appropriate
container such as MKV or explicitly permit transcoding, retaining your source.
Missing audio/video, empty output and duration mismatches are failures even when
the native encoder exits successfully. HDR tone mapping and preservation of all
ancillary streams during transcoding are not implemented.

Full YouTube extraction needs a supported JS runtime and yt-dlp-ejs in addition to
FFmpeg. See upstream's EJS guide. Captured `blob:` URLs and isolated media segments
are not interchangeable with a complete downloadable video or manifest.
