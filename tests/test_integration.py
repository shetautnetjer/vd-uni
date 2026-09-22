"""Offline end-to-end downloads against a loopback-only synthetic media server."""
import functools
import http.server
import importlib.util
import shutil
import subprocess
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path

from vd.core.config import DEFAULT_SETTINGS
from vd.downloaders.ytdlp_adapter import build_args
from vd.media import probe_media


@unittest.skipUnless(importlib.util.find_spec('yt_dlp') and shutil.which('ffmpeg'), 'yt-dlp and FFmpeg required')
class DownloadIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = tempfile.TemporaryDirectory(prefix='vd-http-fixtures-')
        cls.root = Path(cls.fixtures.name)
        cls.source = cls.root / 'source.mp4'
        def ffmpeg(*args):
            subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', *map(str, args)], check=True, timeout=30)
        ffmpeg('-f', 'lavfi', '-i', 'testsrc2=size=192x108:rate=10:duration=2',
               '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=2',
               '-c:v', 'libx264', '-g', '10', '-threads', '1', '-c:a', 'aac', '-shortest', cls.source)
        for extension in ('mkv', 'mov', 'avi'):
            ffmpeg('-i', cls.source, '-c', 'copy', cls.root / ('source.' + extension))
        ffmpeg('-i', cls.source, '-c:v', 'libvpx-vp9', '-threads', '1', '-c:a', 'libopus', cls.root / 'source.webm')
        shutil.copyfile(cls.source, cls.root / 'extensionless')
        ffmpeg('-i', cls.source, '-c', 'copy', '-hls_time', '1', '-hls_list_size', '0', '-f', 'hls', cls.root / 'stream.m3u8')
        ffmpeg('-i', cls.source, '-c', 'copy', '-seg_duration', '1', '-f', 'dash', cls.root / 'stream.mpd')
        text = (cls.root / 'stream.m3u8').read_text()
        (cls.root / 'broken.m3u8').write_text('\n'.join('missing.ts' if line.endswith('.ts') else line for line in text.splitlines()))
        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def guess_type(self, path):
                return 'video/mp4' if str(path).endswith('extensionless') else super().guess_type(path)
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(cls.root)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.fixtures.cleanup()

    def download(self, name, directory, **overrides):
        settings = replace(DEFAULT_SETTINGS, output_dir=directory, use_cookies=False, retries=0, socket_timeout=3, **overrides)
        return subprocess.run(build_args(self.base + '/' + name, settings), capture_output=True, text=True, timeout=30)

    def assert_video(self, directory):
        videos = [p for p in Path(directory).iterdir() if p.suffix not in ('.part', '.ytdl')]
        self.assertTrue(videos)
        for output in videos:
            info = probe_media(output)
            self.assertTrue(any(s['codec_type'] == 'video' for s in info['streams']))
            self.assertTrue(any(s['codec_type'] == 'audio' for s in info['streams']))
            self.assertGreater(float(info['format']['duration']), 1.5)

    def test_direct_video_files_and_extensionless_mime(self):
        for name in ('source.mp4', 'source.mkv', 'source.mov', 'source.avi', 'source.webm', 'extensionless'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                result = self.download(name, Path(tmp))
                self.assertEqual(result.returncode, 0, result.stderr[-3000:])
                self.assert_video(tmp)

    def test_hls_and_dash_download_complete_audio_and_video(self):
        for name in ('stream.m3u8', 'stream.mpd'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                result = self.download(name, Path(tmp))
                self.assertEqual(result.returncode, 0, result.stderr[-3000:])
                self.assert_video(tmp)

    def test_missing_hls_segments_report_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.download('broken.m3u8', Path(tmp))
            self.assertNotEqual(result.returncode, 0)

    def test_download_remux_keeps_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.download('source.mp4', Path(tmp), remux_video='mkv')
            self.assertEqual(result.returncode, 0, result.stderr[-3000:])
            self.assertEqual({p.suffix for p in Path(tmp).iterdir()}, {'.mkv', '.mp4'})
            self.assert_video(tmp)
