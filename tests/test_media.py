"""Real, tiny, synthetic video tests. No private media or external sites."""
import hashlib
import importlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'FFmpeg tools not installed')
class MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = tempfile.TemporaryDirectory(prefix='vd-fixtures-')
        cls.source = Path(cls.fixtures.name) / 'source.mkv'
        subprocess.run([
            'ffmpeg', '-v', 'error', '-nostdin', '-f', 'lavfi', '-i',
            'testsrc2=size=192x108:rate=10:duration=1', '-f', 'lavfi', '-i',
            'sine=frequency=440:sample_rate=48000:duration=1',
            '-c:v', 'libx264', '-threads', '1', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-shortest', str(cls.source),
        ], check=True, timeout=30)
        cls.original_hash = hashlib.sha256(cls.source.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.fixtures.cleanup()

    def setUp(self):
        self.work = tempfile.TemporaryDirectory(prefix='vd-media-test-')
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        try:
            self.media = importlib.import_module('vd.media')
        except ModuleNotFoundError:
            self.fail('The local video conversion/probing feature is not implemented')

    def tearDown(self):
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.original_hash)

    def test_content_probe_does_not_require_known_extension(self):
        target = self.root / 'camera download.anything'
        shutil.copyfile(self.source, target)
        info = self.media.probe_media(target)
        self.assertTrue(any(s['codec_type'] == 'video' for s in info['streams']))

    def test_lossless_remux_is_default_when_compatible(self):
        result = self.media.convert_media(self.source, self.root / 'copy.mp4')
        self.assertEqual((result.engine, result.mode), ('ffmpeg', 'copy'))
        info = self.media.probe_media(result.output)
        self.assertEqual([s['codec_name'] for s in info['streams']], ['h264', 'aac'])

    def test_transcode_output_matrix(self):
        for suffix in ('mp4', 'mkv', 'mov', 'webm', 'avi', 'ts', 'mpg', 'flv', 'ogv', 'wmv'):
            with self.subTest(suffix=suffix):
                result = self.media.convert_media(self.source, self.root / ('video.' + suffix), mode='transcode')
                info = self.media.probe_media(result.output)
                self.assertTrue(any(s['codec_type'] == 'video' for s in info['streams']))
                self.assertTrue(any(s['codec_type'] == 'audio' for s in info['streams']))
                restored = self.media.convert_media(result.output, self.root / (suffix + '-restored.mp4'))
                self.assertTrue(restored.output.is_file())

    def test_auto_transcodes_incompatible_webm(self):
        result = self.media.convert_media(self.source, self.root / 'out.webm')
        self.assertEqual(result.mode, 'transcode')
        names = [s['codec_name'] for s in self.media.probe_media(result.output)['streams'] if s['codec_type'] in ('video', 'audio')]
        self.assertEqual(names, ['vp9', 'opus'])

    def test_copy_only_does_not_silently_transcode(self):
        target = self.root / 'out.webm'
        with self.assertRaises(self.media.MediaError):
            self.media.convert_media(self.source, target, mode='copy')
        self.assertFalse(target.exists())
        self.assertEqual(list(self.root.iterdir()), [])

    def test_existing_output_is_protected(self):
        target = self.root / 'out.mp4'
        target.write_bytes(b'valuable original')
        with self.assertRaises(self.media.MediaError):
            self.media.convert_media(self.source, target)
        self.assertEqual(target.read_bytes(), b'valuable original')

    def test_explicit_overwrite_is_atomic(self):
        target = self.root / 'out.mp4'
        target.write_bytes(b'old content')
        self.media.convert_media(self.source, target, overwrite=True)
        self.assertGreater(target.stat().st_size, 1000)

    def test_failure_never_destroys_existing_output(self):
        target = self.root / 'out.mp4'
        target.write_bytes(b'valuable original')
        bad = self.root / 'bad.avi'
        bad.write_bytes(b'not a video')
        with self.assertRaises(self.media.MediaError):
            self.media.convert_media(bad, target, overwrite=True)
        self.assertEqual(target.read_bytes(), b'valuable original')
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ['bad.avi', 'out.mp4'])

    def test_same_file_is_rejected_even_with_overwrite(self):
        with self.assertRaises(self.media.MediaError):
            self.media.convert_media(self.source, self.source, overwrite=True)

    def test_hard_link_to_input_is_rejected(self):
        target = self.root / 'same.mp4'
        target.hardlink_to(self.source)
        with self.assertRaises(self.media.MediaError):
            self.media.convert_media(self.source, target, overwrite=True)

    def test_shell_characters_in_paths_are_just_paths(self):
        src = self.root / "input with 'quotes';$().mkv"
        shutil.copyfile(self.source, src)
        dst = self.root / "output with 'quotes';$().mp4"
        self.media.convert_media(src, dst)
        self.assertTrue(dst.is_file())

    def test_timeout_removes_partial_output(self):
        target = self.root / 'timeout.mp4'
        with self.assertRaises(self.media.MediaError):
            self.media.convert_media(self.source, target, mode='transcode', timeout=0.00001)
        self.assertFalse(target.exists())

    def test_rejects_invalid_settings_before_conversion(self):
        for kwargs in ({'engine': 'bogus'}, {'mode': 'bogus'}, {'timeout': 0}, {'video_encoder': '--exec'}, {'mode': 'copy', 'video_encoder': 'h264_nvenc'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(self.media.MediaError):
                self.media.convert_media(self.source, self.root / 'out.mp4', **kwargs)

    def test_empty_successful_process_is_not_a_successful_conversion(self):
        with patch.object(self.media, '_run_media', return_value=None):
            with self.assertRaises(self.media.MediaError):
                self.media.convert_media(self.source, self.root / 'empty.mp4', engine='ffmpeg')

    @unittest.skipUnless(shutil.which('cvlc') or shutil.which('vlc'), 'VLC not installed')
    def test_vlc_transcodes_and_validates_audio_and_video(self):
        for suffix, codecs in (('mp4', ['h264', 'aac']), ('ogv', ['theora', 'vorbis'])):
            with self.subTest(suffix=suffix):
                result = self.media.convert_media(self.source, self.root / ('vlc.' + suffix), engine='vlc', mode='transcode')
                self.assertEqual(result.engine, 'vlc')
                names = [s['codec_name'] for s in self.media.probe_media(result.output)['streams'] if s['codec_type'] in ('video', 'audio')]
                self.assertCountEqual(names, codecs)

    @unittest.skipUnless(shutil.which('cvlc') or shutil.which('vlc'), 'VLC not installed')
    def test_auto_falls_back_to_vlc_when_ffmpeg_missing(self):
        real_find = self.media.find_tool
        with patch.object(self.media, 'find_tool', side_effect=lambda name: None if name == 'ffmpeg' else real_find(name)):
            result = self.media.convert_media(self.source, self.root / 'fallback.mp4')
        self.assertEqual(result.engine, 'vlc')
