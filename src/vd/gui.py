from __future__ import annotations

import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from vd.core.config import Settings, ensure_config_files, load_settings
from vd.downloaders.ytdlp_adapter import build_args


class DownloaderApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("VD-uni Downloader")
        self.geometry("760x520")

        self._log_queue: queue.Queue[str] = queue.Queue()
        self._download_thread: threading.Thread | None = None
        self._proc: subprocess.Popen[str] | None = None

        self._init_ui()
        self.after(100, self._drain_logs)

    def _init_ui(self) -> None:
        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Video URL").pack(anchor="w")
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(container, textvariable=self.url_var)
        url_entry.pack(fill="x")

        ttk.Label(container, text="Output folder").pack(anchor="w", pady=(12, 0))
        output_row = ttk.Frame(container)
        output_row.pack(fill="x")
        self.output_var = tk.StringVar()
        output_entry = ttk.Entry(output_row, textvariable=self.output_var)
        output_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(output_row, text="Browse…", command=self._pick_output).pack(
            side="left", padx=(8, 0)
        )

        self.download_btn = ttk.Button(container, text="Download", command=self._download)
        self.download_btn.pack(anchor="w", pady=(12, 0))

        ttk.Label(container, text="Log").pack(anchor="w", pady=(12, 0))
        self.log_text = tk.Text(container, height=18, wrap="none")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

    def _pick_output(self) -> None:
        folder = filedialog.askdirectory(title="Choose output folder")
        if folder:
            self.output_var.set(folder)

    def _append_log(self, line: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _drain_logs(self) -> None:
        try:
            while True:
                line = self._log_queue.get_nowait()
                self._append_log(line)
        except queue.Empty:
            pass
        self.after(100, self._drain_logs)

    def _download(self) -> None:
        if self._download_thread and self._download_thread.is_alive():
            return

        url = self.url_var.get().strip()
        output_dir = self.output_var.get().strip()

        if not url:
            self._append_log("Please enter a URL.\n")
            return

        if not output_dir:
            self._append_log("Please choose an output folder.\n")
            return

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        settings = load_settings()
        settings = Settings(
            output_dir=out_path,
            quality=settings.quality,
            use_cookies=settings.use_cookies,
            live_from_start=settings.live_from_start,
            per_site_cookies=settings.per_site_cookies,
        )

        args = build_args(url, settings)
        self.download_btn.configure(state="disabled")
        self._append_log(f"Starting download: {url}\n")

        def _run() -> None:
            try:
                self._proc = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                assert self._proc.stdout is not None
                for line in self._proc.stdout:
                    self._log_queue.put(line)
                rc = self._proc.wait()
                self._log_queue.put(f"Download finished (code {rc}).\n")
            except Exception as exc:
                self._log_queue.put(f"Download failed: {exc}\n")
            finally:
                self._proc = None
                self.download_btn.configure(state="normal")

        self._download_thread = threading.Thread(target=_run, daemon=True)
        self._download_thread.start()


def main() -> int:
    ensure_config_files()
    settings = load_settings()
    app = DownloaderApp()
    app.output_var.set(str(settings.output_dir))
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
