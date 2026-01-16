from __future__ import annotations

import argparse
from pathlib import Path

from vd.core.config import ensure_config_files, load_settings
from vd.core.logging_setup import configure_logging
from vd.downloaders.ytdlp_adapter import run_downloads
from vd.updaters.update import update_tools


def _print_commands() -> None:
    commands_file = Path(__file__).resolve().parents[3] / "commands"
    if commands_file.exists():
        print(commands_file.read_text(encoding="utf-8"))
    else:
        print("commands file not found")


def _load_url_list(path: Path) -> list[str]:
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("#"):
            continue
        urls.append(cleaned)
    return urls


def _read_version_file() -> str | None:
    version_file = Path(__file__).resolve().parents[3] / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return None


def _print_version() -> None:
    version = _read_version_file()
    print(version if version else "unknown")


def _bump_version(part: str) -> int:
    version_file = Path(__file__).resolve().parents[3] / "VERSION"
    current = _read_version_file()
    if not current:
        print("unknown")
        return 1
    try:
        major_s, minor_s, patch_s = current.split(".")
        major, minor, patch = int(major_s), int(minor_s), int(patch_s)
    except ValueError:
        print("invalid version format; expected X.Y.Z")
        return 1

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    new_version = f"{major}.{minor}.{patch}"
    version_file.write_text(new_version + "\n", encoding="utf-8")
    print(new_version)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vd")
    sub = parser.add_subparsers(dest="cmd")

    dl = sub.add_parser("download", help="Download a video by URL")
    dl.add_argument("url", nargs="*")
    dl.add_argument("--file", dest="url_file", help="File with URLs (one per line)")

    upd = sub.add_parser("update", help="Update tools (yt-dlp)")
    upd.add_argument("--pip", default="python")

    ck = sub.add_parser("cookies", help="Export cookies from a browser")
    ck.add_argument("--browser", required=True, choices=["chrome", "chromium", "brave", "firefox"])
    ck.add_argument("--domain", required=True)
    ck.add_argument("--output")

    sub.add_parser("help", help="Show commands")
    sub.add_parser("commands", help="Show commands")
    ver = sub.add_parser("version", help="Show VD-uni version")
    ver.add_argument("--bump", choices=["major", "minor", "patch"])

    args = parser.parse_args(argv)

    logger = configure_logging()
    ensure_config_files()

    if args.cmd == "download":
        settings = load_settings()
        settings.output_dir.mkdir(parents=True, exist_ok=True)
        urls: list[str] = []
        if args.url_file:
            path = Path(args.url_file)
            if not path.exists():
                logger.error("URL file not found: %s", path)
                return 2
            urls.extend(_load_url_list(path))
        urls.extend(args.url or [])

        if not urls:
            logger.error("No URLs provided. Use a URL or --file.")
            return 2

        logger.info("Starting download for %s url(s)", len(urls))
        rc = run_downloads(urls, settings)
        if rc != 0:
            logger.error("Download failed with code %s", rc)
        return rc

    if args.cmd == "update":
        logger.info("Updating tools...")
        rc = update_tools(args.pip)
        if rc != 0:
            logger.error("Update failed with code %s", rc)
        return rc

    if args.cmd == "cookies":
        from vd.utils.cookie_export import export_cookies

        logger.info("Exporting cookies for %s (%s)", args.domain, args.browser)
        rc = export_cookies(args.browser, args.domain, args.output)
        if rc != 0:
            logger.error("Cookie export failed with code %s", rc)
        return rc

    if args.cmd in {"help", "commands"}:
        _print_commands()
        return 0

    if args.cmd == "version":
        if args.bump:
            return _bump_version(args.bump)
        _print_version()
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
