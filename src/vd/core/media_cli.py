"""CLI surfaces for media operations; diagnostic commands do not write config."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import shutil
import subprocess

from vd.core.config import load_settings
from vd.downloaders.ytdlp_adapter import run_download
from vd.media import PROFILES, VLC_PROFILES, MediaError, convert_media, find_tool, probe_media

MEDIA_COMMANDS = {'convert', 'probe', 'formats', 'doctor'}


def add_media_commands(sub: argparse._SubParsersAction) -> None:
    convert = sub.add_parser('convert', help='Convert any locally decodable video, preserving the source')
    convert.add_argument('input')
    convert.add_argument('-o', '--output', required=True)
    convert.add_argument('--engine', choices=['auto', 'ffmpeg', 'vlc'], default='auto')
    convert.add_argument('--mode', choices=['auto', 'copy', 'transcode'], default='auto')
    convert.add_argument('--overwrite', action='store_true')
    convert.add_argument('--timeout', type=float, default=3600, help='Total deadline in seconds')
    convert.add_argument('--video-encoder', help='FFmpeg encoder, e.g. h264_nvenc; requires --mode transcode')
    probe = sub.add_parser('probe', help='Inspect actual streams/codecs, independent of filename extension')
    probe.add_argument('input')
    formats = sub.add_parser('formats', help='Show installed capabilities or list a URL\'s available formats')
    formats.add_argument('url', nargs='?')
    formats.add_argument('--full', action='store_true', help='List all FFmpeg formats and encoders')
    doctor = sub.add_parser('doctor', help='Check installed dependencies without changing the system')
    doctor.add_argument('--json', action='store_true')
    doctor.add_argument('--redact', action='store_true', help='Omit installation paths from shareable diagnostics')


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def environment_report() -> dict:
    report = {'python': platform.python_version(), 'yt_dlp': _package_version('yt-dlp'),
              'yt_dlp_ejs': _package_version('yt-dlp-ejs')}
    for name in ('ffmpeg', 'ffprobe', 'vlc'):
        tool = find_tool(name)
        version = None
        if tool:
            try:
                flag = '--version' if name == 'vlc' else '-version'
                proc = subprocess.run([tool, flag], capture_output=True, text=True, timeout=5, check=False)
                if proc.returncode == 0 and proc.stdout:
                    version = proc.stdout.splitlines()[0]
            except (OSError, subprocess.TimeoutExpired):
                pass
        report[name] = {'path': tool, 'version': version}
    report['javascript_runtimes'] = {name: shutil.which(name) for name in ('deno', 'node', 'bun', 'qjs')}
    report['ffmpeg_profiles'] = sorted(PROFILES)
    report['vlc_profiles'] = sorted(VLC_PROFILES)
    return report


def run_media_command(args: argparse.Namespace) -> int:
    if args.cmd == 'probe':
        print(json.dumps(probe_media(args.input), indent=2))
        return 0
    if args.cmd == 'convert':
        result = convert_media(args.input, args.output, engine=args.engine, mode=args.mode,
                               overwrite=args.overwrite, timeout=args.timeout, video_encoder=args.video_encoder)
        print(f'{result.output}\nBackend: {result.engine}; operation: {result.mode}; elapsed: {result.elapsed_seconds:.2f}s')
        for warning in result.warnings:
            print(f'Note: {warning}')
        return 0
    if args.cmd == 'formats':
        if args.url:
            return run_download(args.url, load_settings(), list_formats=True)
        print('Input: any local video that the installed ffprobe can inspect; no extension whitelist.')
        print('FFmpeg tuned output profiles: ' + ', '.join(sorted(PROFILES)))
        print('Other FFmpeg outputs use its installed muxer/encoder defaults.')
        print('VLC output profiles: ' + ', '.join(sorted(VLC_PROFILES)))
        print('Compiled hardware encoders do not prove that a working GPU/driver is available.')
        if args.full:
            tool = find_tool('ffmpeg')
            if not tool:
                raise MediaError('Install FFmpeg to list its available formats and encoders')
            for flag in ('-formats', '-encoders'):
                try:
                    proc = subprocess.run([tool, '-hide_banner', flag], check=False, timeout=15)
                except subprocess.TimeoutExpired as exc:
                    raise MediaError('FFmpeg capability listing timed out') from exc
                if proc.returncode:
                    return proc.returncode
        return 0
    report = environment_report()
    if args.redact:
        for name in ('ffmpeg', 'ffprobe', 'vlc'):
            state = report[name]
            state['available'] = bool(state.pop('path'))
        report['javascript_runtimes'] = {name: bool(path) for name, path in report['javascript_runtimes'].items()}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print('Python: ' + report['python'])
        print('yt-dlp: ' + (report['yt_dlp'] or 'MISSING; install requirements.txt'))
        for name in ('ffmpeg', 'ffprobe', 'vlc'):
            state = report[name]
            print(f'{name}: {state["version"] or state.get("path") or ("installed" if state.get("available") else "not installed")}')
        print('VLC is optional. ffprobe is required even for VLC output validation.')
        print('Full YouTube support additionally requires yt-dlp-ejs and a supported JS runtime; Deno is detected by yt-dlp automatically.')
    return 0 if report['yt_dlp'] and report['ffmpeg']['version'] and report['ffprobe']['version'] else 1
