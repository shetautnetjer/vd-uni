# Media processing and limits

## Backend strategy

Website extraction and HLS/DASH assembly stay with yt-dlp. FFmpeg and VLC are
invoked as external programs, never by constructing shell commands. VD-uni does
not vendor or relicense either project's source code. Their own distribution and
build licensing remains applicable.

The local `convert` command probes input, tries a stream-copy remux first, and
only then attempts a compatibility transcode. The optional VLC fallback is
independent of the FFmpeg executable, but **not independent of ffprobe**, which is
required to validate both source and output. `--engine ffmpeg` or `--engine vlc`
disables cross-backend fallback. Explicit `--video-encoder` requests use FFmpeg
only and require `--mode transcode`; they are never silently replaced by VLC.

FFmpeg encoders being listed does not prove that a GPU or driver is functional.
GPU passthrough and driver installation are out of scope. No GPU acceleration
performance has been measured for this change.

VLC output is deliberately limited to MP4/M4V and OGV/OGG. The tested VLC build
produced audio-only output for a one-second TS transcode, so that path is not
advertised or silently accepted. FFmpeg remains available for TS conversion.

## Source protection and validation

Local inputs must be regular files, not network URLs. Source files with unknown
extensions work when their content is supported. FFmpeg/ffprobe conversion access
is limited to local protocols; use `download` for remote manifests. Conversion is
not a sandbox for hostile files: run it in a restricted container when appropriate.

A private staging directory is created beside the destination. FFmpeg/VLC writes
there, then ffprobe checks that output contains real video rather than just cover
art, has the expected number of audio tracks, and has a duration within 2% or one
second of the original when known. Copy mode additionally requires the same
codec/type inventory. These are structural checks, **not an exhaustive decode of
every frame**. A zero encoder exit status alone is never sufficient.

Publication is atomic. Without overwrite, a hard link creates the destination only
if it does not exist, protecting against another writer. Filesystems without hard
link support produce an explicit error rather than unsafe overwriting. With
explicit overwrite, replacement happens only after validation. Source aliases,
including hard links, and output symlinks are rejected. Failed staging artifacts
are cleaned up. A single timeout budget covers probing and all conversion attempts.

## Quality and streams

Remuxing copies compressed streams without generation loss. Transcoding uses
bounded CPU threads and format-appropriate codecs. Common MP4/MOV/MKV profiles use
H.264/AAC; WebM uses VP9/Opus. The compatibility encoder pads odd dimensions and
outputs 8-bit yuv420p. It does not implement HDR tone mapping or professional
color-management guarantees. A transcode may discard subtitles, attachments,
data streams, and additional video angles. This is reported; originals remain.

Use `--mode copy` when preserving stream inventory is mandatory. Unsupported
container/codec combinations then fail rather than silently losing tracks or
re-encoding. A stream inventory check does not guarantee every metadata field is
identical across different containers.

## Dependency references

- FFmpeg command and stream-copy documentation: https://ffmpeg.org/ffmpeg.html
- FFmpeg container support: https://ffmpeg.org/ffmpeg-formats.html
- VLC source and developer documentation: https://www.videolan.org/developers/vlc.html
- VLC transcode-and-save documentation: https://docs.videolan.me/vlc-user/desktop/3.0/en/advanced/transcode/transcode_and_save.html
- yt-dlp documentation: https://github.com/yt-dlp/yt-dlp

Actual codec availability depends on the installed builds; `vd formats --full`
reports those capabilities rather than relying on a hardcoded claim of universality.
