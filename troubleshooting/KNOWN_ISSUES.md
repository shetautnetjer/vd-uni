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
