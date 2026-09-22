import contextlib
import importlib
import io
import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from vd.utils import cookie_export


class CookiePrivacyTests(unittest.TestCase):
    def row(self, value='test-cookie-value'):
        return cookie_export.CookieRow('.example.com', True, '/', True, 0, 'session', value)

    def test_cookie_file_is_owner_only_even_after_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'cookies.txt'
            output.write_text('old')
            output.chmod(0o644)
            cookie_export._write_netscape(output, [self.row()])
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertIn('test-cookie-value', output.read_text())

    def test_cookie_writer_does_not_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / 'original'
            original.write_text('keep this')
            output = Path(tmp) / 'cookies.txt'
            output.symlink_to(original)
            with self.assertRaises(ValueError):
                cookie_export._write_netscape(output, [self.row()])
            self.assertEqual(original.read_text(), 'keep this')

    def test_cookie_control_characters_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'cookies.txt'
            with self.assertRaises(ValueError):
                cookie_export._write_netscape(output, [self.row('first\nsecond')])
            self.assertFalse(output.exists())

    def test_bad_domain_is_rejected_before_opening_browser(self):
        for domain in ('../../outside', 'https://example.com', '', 'example.com:443', 'a b.com'):
            with self.subTest(domain=domain), tempfile.TemporaryDirectory() as tmp, patch.object(cookie_export, 'COOKIES_DIR', Path(tmp) / 'nested' / 'cookies'), patch.object(cookie_export, '_browser_getters') as getters:
                with self.assertRaises(ValueError):
                    cookie_export.export_cookies('chrome', domain)
                getters.assert_not_called()

    def test_export_normalizes_domain_and_filters_unrelated_cookies(self):
        def cookie(domain):
            return SimpleNamespace(domain=domain, path='/', secure=True, expires=0, name='session', value='fixture')
        seen = []
        def getter(**kwargs):
            seen.append(kwargs)
            return [cookie('.example.com'), cookie('media.example.com'), cookie('notexample.com')]
        with tempfile.TemporaryDirectory() as tmp, patch.object(cookie_export, 'COOKIES_DIR', Path(tmp)), patch.object(cookie_export, '_browser_getters', return_value={'chrome': getter}), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cookie_export.export_cookies('chrome', 'WWW.Example.COM'), 0)
            text = (Path(tmp) / 'example.com.txt').read_text()
            self.assertIn('media.example.com', text)
            self.assertNotIn('notexample.com', text)
            self.assertNotIn(tmp, out.getvalue())
            self.assertEqual(seen, [{'domain_name': 'example.com'}])


class OutputPrivacyTests(unittest.TestCase):
    def privacy(self):
        try:
            return importlib.import_module('vd.utils.privacy')
        except ModuleNotFoundError:
            self.fail('Output redaction is not implemented')

    def test_signed_urls_remove_credentials_queries_and_fragments(self):
        redact = self.privacy().redact_text
        message = 'Error https://viewer:password@example.com/private/movie.mp4?signature=fixture-signature#fixture-fragment'
        result = redact(message)
        for private in ('viewer', 'password', 'signature=', 'fixture-signature', 'fixture-fragment', '/private/movie'):
            self.assertNotIn(private, result)
        self.assertIn('example.com', result)

    def test_malformed_url_is_redacted_not_repeated(self):
        result = self.privacy().redact_text('https://[invalid?key=private-value')
        self.assertNotIn('private-value', result)

    def test_known_local_roots_are_not_displayed(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.privacy().redact_text(f'Cannot open {tmp}/a.mp4', roots=[tmp])
        self.assertNotIn(tmp, result)

    def test_portable_doctor_has_no_executable_paths(self):
        from vd.core.cli import main
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertIn(main(['doctor', '--json', '--redact']), (0, 1))
        import json
        report = json.loads(out.getvalue())
        for name in ('ffmpeg', 'ffprobe', 'vlc'):
            self.assertNotIn('path', report[name])
            self.assertIn('available', report[name])
        for value in report['javascript_runtimes'].values():
            self.assertIsInstance(value, bool)

    def test_cli_download_output_is_redacted(self):
        from vd.core.config import DEFAULT_SETTINGS
        from vd.downloaders.ytdlp_adapter import run_download
        from unittest.mock import MagicMock
        proc = MagicMock()
        proc.__enter__.return_value = proc
        proc.stdout = io.StringIO('https://viewer:password@example.com/movie?signature=fixture-signature\n')
        proc.wait.return_value = 3
        with patch('vd.downloaders.ytdlp_adapter.subprocess.Popen', return_value=proc), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(run_download('https://example.com/movie', DEFAULT_SETTINGS), 3)
        self.assertNotIn('fixture-signature', out.getvalue())
        self.assertNotIn('password', out.getvalue())
