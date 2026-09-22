import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from vd.core.config import DEFAULT_SETTINGS, load_settings
from vd.downloaders.ytdlp_adapter import build_args, run_downloads
from vd.utils.url import extract_domain


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.settings = replace(DEFAULT_SETTINGS, use_cookies=False)

    def test_preserves_best_quality(self):
        args = build_args('https://example.com/video', self.settings)
        self.assertEqual(args[args.index('-f') + 1], 'bestvideo+bestaudio/best')

    def test_hls_never_requests_unplayable_formats(self):
        args = build_args('https://example.com/live.m3u8?token=test', self.settings)
        self.assertNotIn('--allow-unplayable-formats', args)
        self.assertIn('--abort-on-unavailable-fragments', args)

    def test_options_are_terminated_before_url(self):
        args = build_args('https://example.com/video', self.settings)
        self.assertEqual(args[-2:], ['--', 'https://example.com/video'])

    def test_output_names_include_id_and_paths_are_not_templates(self):
        args = build_args('https://example.com/video', replace(self.settings, output_dir=Path('100% videos')))
        self.assertIn('%(id)s', args[args.index('-o') + 1])
        self.assertIn('100% videos', args)
        self.assertIn('--no-overwrites', args)
        self.assertIn('--ignore-config', args)

    def test_retries_are_explicit(self):
        args = build_args('https://example.com/video', self.settings)
        for option in ('--retries', '--fragment-retries', '--socket-timeout', '--continue'):
            self.assertIn(option, args)

    def test_credential_and_port_free_cookie_domain(self):
        self.assertEqual(extract_domain('https://user:secret@WWW.Example.COM:443/a'), 'example.com')

    def test_duplicate_urls_do_not_launch_extra_downloads(self):
        with patch('vd.downloaders.ytdlp_adapter.run_download', return_value=0) as run:
            self.assertEqual(run_downloads(['https://example.com/a', ' https://example.com/a ', 'https://example.com/b'], self.settings), 0)
            self.assertEqual(run.call_count, 2)

    def test_failures_are_not_masked_by_later_success(self):
        with patch('vd.downloaders.ytdlp_adapter.run_download', side_effect=[1, 0]):
            self.assertNotEqual(run_downloads(['https://example.com/a', 'https://example.com/b'], self.settings), 0)

    def test_invalid_configuration_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'settings.json'
            for text in ('{"concurrent_fragments": 0}', '{"use_cookies": "false"}', '[]'):
                path.write_text(text)
                with self.subTest(text=text), patch('vd.core.config.CONFIG_FILE', path):
                    with self.assertRaises(ValueError):
                        load_settings()

    def test_empty_batch_fails(self):
        self.assertNotEqual(run_downloads([], self.settings), 0)

    def test_rejects_non_url_input(self):
        for value in ('--exec=touch bad', 'file:///etc/passwd', 'not a url'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_args(value, self.settings)
