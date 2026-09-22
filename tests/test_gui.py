import importlib.util
import io
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


@unittest.skipUnless(importlib.util.find_spec('tkinter') and os.environ.get('DISPLAY'), 'Tk/display not installed; run under xvfb-run')
class GUITests(unittest.TestCase):
    def test_download_preserves_settings_and_updates_widgets_on_main_thread(self):
        from vd.core.config import DEFAULT_SETTINGS
        from vd.gui import DownloaderApp
        from dataclasses import replace
        app = DownloaderApp()
        app.withdraw()
        self.addCleanup(app.destroy)
        with tempfile.TemporaryDirectory() as tmp:
            app.url_var.set('https://example.test/video')
            app.output_var.set(tmp)
            proc = MagicMock()
            proc.stdout = io.StringIO('download progress\n')
            proc.wait.return_value = 0
            calls = []
            configure = app.download_btn.configure
            def checked_configure(*args, **kwargs):
                calls.append(threading.get_ident())
                return configure(*args, **kwargs)
            with patch.object(app.download_btn, 'configure', side_effect=checked_configure), patch('vd.gui.load_settings', return_value=replace(DEFAULT_SETTINGS, concurrent_fragments=8)), patch('vd.gui.build_args', return_value=['test-process']) as build, patch('vd.gui.subprocess.Popen', return_value=proc):
                app._download()
                deadline = time.monotonic() + 3
                while app._download_thread and app._download_thread.is_alive() and time.monotonic() < deadline:
                    app.update()
                    time.sleep(0.01)
                app._drain_logs()
                self.assertFalse(app._download_thread.is_alive())
                self.assertEqual(build.call_args.args[1].concurrent_fragments, 8)
                self.assertEqual(str(app.download_btn['state']), 'normal')
                self.assertTrue(all(t == threading.get_ident() for t in calls))
