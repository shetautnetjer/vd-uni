from __future__ import annotations

import subprocess
from typing import Iterable


def update_tools(pip: str = "python") -> int:
    cmd = [pip, "-m", "pip", "install", "-U", "yt-dlp"]
    proc = subprocess.run(cmd, check=False)
    return proc.returncode
