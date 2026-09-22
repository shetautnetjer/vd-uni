"""Validated local video conversion through installed FFmpeg and VLC tools."""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class MediaError(RuntimeError):
    """An actionable media error."""


@dataclass(frozen=True)
class ConversionResult:
    output: Path
    engine: str
    mode: str
    elapsed_seconds: float
    warnings: tuple[str, ...] = ()

PROFILES = {
    'mp4': ('mp4', 'libx264', 'aac'), 'm4v': ('mp4', 'libx264', 'aac'),
    'mov': ('mov', 'libx264', 'aac'), 'mkv': ('matroska', 'libx264', 'aac'),
    'webm': ('webm', 'libvpx-vp9', 'libopus'),
    'avi': ('avi', 'mpeg4', 'libmp3lame'),
    'ts': ('mpegts', 'libx264', 'aac'), 'mts': ('mpegts', 'libx264', 'aac'),
    'm2ts': ('mpegts', 'libx264', 'aac'),
    'mpg': ('mpeg', 'mpeg2video', 'mp2'), 'mpeg': ('mpeg', 'mpeg2video', 'mp2'),
    'flv': ('flv', 'flv', 'libmp3lame'),
    'ogv': ('ogg', 'libtheora', 'libvorbis'), 'ogg': ('ogg', 'libtheora', 'libvorbis'),
    'wmv': ('asf', 'wmv2', 'wmav2'), 'asf': ('asf', 'wmv2', 'wmav2'),
}
VLC_PROFILES = {
    'mp4': ('mp4', 'h264', 'mp4a'), 'm4v': ('mp4', 'h264', 'mp4a'),
    'ogv': ('ogg', 'theo', 'vorb'), 'ogg': ('ogg', 'theo', 'vorb'),
}


def find_tool(name: str) -> str | None:
    override = os.environ.get(f'VD_{name.upper()}')
    if override:
        return shutil.which(override)
    if name == 'vlc':
        return shutil.which('cvlc') or shutil.which('vlc')
    return shutil.which(name)


def probe_media(path: Path | str, *, timeout: float = 30) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise MediaError('Input must be an existing regular local file')
    tool = find_tool('ffprobe')
    if not tool:
        raise MediaError('ffprobe is required for validation; install FFmpeg')
    args = [tool, '-v', 'error', '-protocol_whitelist', 'file,pipe,crypto,data',
            '-show_entries', 'format=format_name,duration,size:stream=index,codec_type,codec_name,width,height:stream_disposition=attached_pic',
            '-of', 'json', '-i', str(source)]
    try:
        proc = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True,
                              check=False, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise MediaError('Media probe timed out') from exc
    except OSError as exc:
        raise MediaError(f'Could not run ffprobe: {exc.strerror}') from exc
    if proc.returncode:
        detail = proc.stderr[-3000:].decode('utf-8', errors='replace').strip()
        raise MediaError(f'ffprobe could not read this media: {detail}')
    try:
        info = json.loads(proc.stdout)
    except (ValueError, UnicodeDecodeError) as exc:
        raise MediaError('ffprobe returned invalid JSON') from exc
    if not isinstance(info, dict) or not isinstance(info.get('streams'), list):
        raise MediaError('ffprobe returned no stream information')
    return info


def _video_streams(info: dict[str, Any]) -> list[dict[str, Any]]:
    return [s for s in info['streams'] if s.get('codec_type') == 'video'
            and not s.get('disposition', {}).get('attached_pic')]


def _duration(info: dict[str, Any]) -> float | None:
    try:
        value = float(info.get('format', {}).get('duration', 0))
        return value if math.isfinite(value) and value > 0 else None
    except (TypeError, ValueError):
        return None


def _run_media(args: list[str], *, cwd: Path, timeout: float) -> None:
    with tempfile.TemporaryFile() as errors:
        try:
            proc = subprocess.run(args, cwd=cwd, stdin=subprocess.DEVNULL,
                                  stdout=subprocess.DEVNULL, stderr=errors,
                                  check=False, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise MediaError('Conversion timed out; partial output discarded') from exc
        except OSError as exc:
            raise MediaError(f'Could not start media tool: {exc.strerror}') from exc
        if proc.returncode:
            errors.seek(0, os.SEEK_END)
            errors.seek(max(0, errors.tell() - 4000))
            detail = errors.read().decode('utf-8', errors='replace').strip()
            raise MediaError(f'Media tool exited {proc.returncode}: {detail}')


def _ffmpeg_args(tool: str, source: Path, output: Path, mode: str,
                 video_encoder: str | None) -> list[str]:
    suffix = output.suffix.lower().lstrip('.')
    profile = PROFILES.get(suffix)
    args = [tool, '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
            '-protocol_whitelist', 'file,pipe,crypto,data', '-i', str(source)]
    if mode == 'copy':
        args += ['-map', '0', '-c', 'copy']
    else:
        args += ['-map', '0:V:0', '-map', '0:a?', '-sn', '-dn']
        encoder = video_encoder or (profile[1] if profile else None)
        if encoder:
            args += ['-c:v', encoder]
        if profile:
            args += ['-c:a', profile[2]]
        args += ['-threads', '2', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-pix_fmt', 'yuv420p']
        if encoder in ('libx264', 'libx265'):
            args += ['-preset', 'medium', '-crf', '23']
        elif encoder == 'libvpx-vp9':
            args += ['-crf', '32', '-b:v', '0', '-row-mt', '1', '-cpu-used', '2']
        elif encoder and encoder.endswith('_nvenc'):
            args += ['-preset', 'p4', '-cq', '23']
        elif encoder in ('mpeg4', 'mpeg2video', 'wmv2', 'flv'):
            args += ['-q:v', '5']
        elif encoder == 'libtheora':
            args += ['-q:v', '7']
        if suffix == 'flv':
            args += ['-ar', '44100']
    args += ['-map_metadata', '0', '-map_chapters', '0']
    if suffix in ('mp4', 'm4v', 'mov'):
        args += ['-movflags', '+faststart']
    if profile:
        args += ['-f', profile[0]]
    return args + [str(output)]


def _vlc_args(tool: str, source: Path, output: Path, mode: str) -> list[str]:
    suffix = output.suffix.lower().lstrip('.')
    if suffix not in VLC_PROFILES:
        raise MediaError(f'VLC output .{suffix} is not supported by this adapter; use FFmpeg')
    mux, video, audio = VLC_PROFILES[suffix]
    chain = '#'
    if mode == 'transcode':
        chain += f'transcode{{vcodec={video},acodec={audio},vb=4000,ab=192,threads=2}}:'
    # A generated basename enters sout, never user text. cwd is the staging dir.
    chain += f'std{{access=file,mux={mux},dst={output.name}}}'
    return [tool, '--intf=dummy', '--ignore-config', '--no-media-library',
            '--no-repeat', '--no-loop', '--no-video-title-show', '--sout-all',
            '--sout', chain, '--', source.as_uri(), 'vlc://quit']


def _validate_output(path: Path, original: dict[str, Any], mode: str, timeout: float) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise MediaError('Encoder produced no media, despite possibly exiting successfully')
    result = probe_media(path, timeout=timeout)
    videos = _video_streams(result)
    if not videos or any(not s.get('codec_name') or s.get('width', 0) <= 0 or s.get('height', 0) <= 0 for s in videos):
        raise MediaError('Output validation failed: no fully identified video stream')
    count_audio = lambda info: sum(s.get('codec_type') == 'audio' for s in info['streams'])
    if count_audio(result) != count_audio(original):
        raise MediaError('Output validation failed: audio tracks were lost or added')
    if mode == 'copy':
        signature = lambda info: sorted((s.get('codec_type', ''), s.get('codec_name', '')) for s in info['streams'])
        if signature(result) != signature(original):
            raise MediaError('Remux validation failed: streams/codecs changed')
    before, after = _duration(original), _duration(result)
    if before and (not after or abs(before - after) > max(1.0, before * 0.02)):
        raise MediaError('Output validation failed: missing or materially different duration')


def convert_media(source: Path | str, output: Path | str, *, engine: str = 'auto',
                  mode: str = 'auto', overwrite: bool = False, timeout: float = 3600,
                  video_encoder: str | None = None) -> ConversionResult:
    """Remux before encoding; validate before publishing; never modify input."""
    if engine not in ('auto', 'ffmpeg', 'vlc') or mode not in ('auto', 'copy', 'transcode'):
        raise MediaError('engine must be auto/ffmpeg/vlc; mode must be auto/copy/transcode')
    if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise MediaError('timeout must be a finite positive number of seconds')
    if video_encoder and (not re.fullmatch(r'[A-Za-z0-9_]{1,100}', video_encoder)
                          or mode != 'transcode' or engine == 'vlc'):
        raise MediaError('An explicit video encoder requires --mode transcode and FFmpeg')
    started = time.monotonic()

    def remaining() -> float:
        seconds = timeout - (time.monotonic() - started)
        if seconds <= 0:
            raise MediaError('Conversion timed out; partial output discarded')
        return seconds

    src = Path(source).expanduser().resolve()
    dst = Path(os.path.abspath(Path(output).expanduser()))
    if not src.is_file():
        raise MediaError('Input must be an existing regular local file')
    if src == dst or (dst.exists() and os.path.samefile(src, dst)):
        raise MediaError('Input and output must be different files')
    if dst.is_symlink():
        raise MediaError('Refusing to replace a symlink output')
    if dst.exists() and not overwrite:
        raise MediaError('Output already exists; pass --overwrite to replace it explicitly')
    if not dst.suffix or not re.fullmatch(r'\.[A-Za-z0-9]{1,12}', dst.suffix):
        raise MediaError('Output needs a media extension, for example .mp4 or .mkv')
    original = probe_media(src, timeout=min(30, remaining()))
    if not _video_streams(original):
        raise MediaError('Input contains no video stream; cover art does not count')
    engines = ['ffmpeg', 'vlc'] if engine == 'auto' else [engine]
    if video_encoder:
        engines = ['ffmpeg']
    modes = ['copy', 'transcode'] if mode == 'auto' else [mode]
    failures: list[str] = []
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.vd-', dir=dst.parent) as stage:
        temporary = Path(stage) / ('output' + dst.suffix.lower())
        for backend in engines:
            tool = find_tool(backend)
            if not tool:
                failures.append(f'{backend}: executable not installed')
                continue
            for attempt in modes:
                try:
                    temporary.unlink(missing_ok=True)
                    args = (_ffmpeg_args(tool, src, temporary, attempt, video_encoder)
                            if backend == 'ffmpeg' else _vlc_args(tool, src, temporary, attempt))
                    _run_media(args, cwd=Path(stage), timeout=remaining())
                    _validate_output(temporary, original, attempt, min(30, remaining()))
                except MediaError as exc:
                    failures.append(f'{backend}/{attempt}: {exc}')
                    continue
                # A publishing error must not trigger a different encoding.
                try:
                    if overwrite:
                        os.replace(temporary, dst)
                    else:
                        os.link(temporary, dst)  # Atomic create-if-absent.
                except OSError as exc:
                    raise MediaError(f'Cannot publish output safely: {exc.strerror}') from exc
                notes: list[str] = []
                if attempt == 'transcode':
                    notes.append('Re-encoding is lossy; the source file was preserved.')
                    extra = any(s.get('codec_type') not in ('video', 'audio') or
                                s.get('disposition', {}).get('attached_pic') for s in original['streams'])
                    if extra or len(_video_streams(original)) > 1:
                        notes.append('Compatibility transcode may omit subtitles, attachments, data, or extra video tracks; use copy mode to require stream preservation.')
                return ConversionResult(dst, backend, attempt, time.monotonic() - started, tuple(notes))
    raise MediaError('No validated output was produced. ' + '\n'.join(failures))
