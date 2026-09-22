import contextlib
import io
import json
import unittest
from unittest.mock import patch

from vd.core.cli import main
from vd.core.config import DEFAULT_SETTINGS


class CLITests(unittest.TestCase):
    def test_new_commands_expose_help(self):
        for command in ('convert', 'probe', 'formats', 'doctor'):
            with self.subTest(command=command), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as result:
                    main([command, '--help'])
                self.assertEqual(result.exception.code, 0)

    def test_download_overrides_do_not_mutate_defaults(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp, patch('vd.core.cli.ensure_config_files'), patch('vd.core.cli.configure_logging'), patch('vd.core.cli.load_settings', return_value=DEFAULT_SETTINGS), patch('vd.core.cli.run_downloads', return_value=0) as run:
            rc = main(['download', 'https://example.com/video', '--output-dir', tmp, '--fragments', '8', '--retries', '3', '--remux', 'mkv', '--no-cookies'])
        self.assertEqual(rc, 0)
        settings = run.call_args.args[1]
        self.assertEqual((settings.output_dir, settings.concurrent_fragments, settings.retries, settings.remux_video, settings.use_cookies), (Path(tmp), 8, 3, 'mkv', False))
        self.assertEqual(DEFAULT_SETTINGS.concurrent_fragments, 4)

    def test_bad_config_is_reported_without_traceback(self):
        with patch('vd.core.cli.ensure_config_files'), patch('vd.core.cli.configure_logging'), patch('vd.core.cli.load_settings', side_effect=ValueError('Invalid settings')), contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(main(['download', 'https://example.com/video']), 2)
        self.assertNotIn('Traceback', err.getvalue())

    def test_missing_local_input_is_reported_without_traceback(self):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(main(['convert', '/nonexistent/vd-test-input', '-o', '/tmp/vd-test-output.mp4']), 2)
        self.assertNotIn('Traceback', err.getvalue())

    def test_doctor_json_is_machine_readable(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            rc = main(['doctor', '--json'])
        self.assertIn(rc, (0, 1))
        report = json.loads(out.getvalue())
        self.assertIn('ffmpeg', report)
        self.assertIn('ffprobe', report)
        self.assertIn('vlc', report)
