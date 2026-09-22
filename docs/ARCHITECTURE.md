# Architecture

- `src/vd/core/cli.py`: download/cookie/update/version entry points and overrides.
- `src/vd/core/media_cli.py`: conversion, probe, formats and dependency diagnostics.
- `src/vd/core/config.py`: validated settings and cookie locations.
- `src/vd/downloaders/ytdlp_adapter.py`: safe yt-dlp argv, retries, stream integrity,
  cookie preference, ordered batch deduplication.
- `src/vd/media.py`: content probe, FFmpeg/VLC adapters, timeout accounting,
  stream validation and atomic output publication.
- `src/vd/gui.py`: Tk downloader; workers emit queue events, widgets update only
  on the main UI thread.
- `extensions/vd-uni-chrome`: opt-in response classification and bounded serialized
  local URL storage. No native browser-to-shell bridge is installed.
- `tests/`: unit, real-media, container-loopback download, GUI and extension tests.

Remote download and local conversion are distinct operations. There is no
attempt to treat arbitrary webpage HTML as a video or to solve unsupported DRM.
The optional VLC backend is integrated through its CLI, not a fork of its source.
