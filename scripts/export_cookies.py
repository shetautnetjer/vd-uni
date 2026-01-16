#!/usr/bin/env python3
from __future__ import annotations

import argparse

from vd.utils.cookie_export import export_cookies


def main() -> int:
    parser = argparse.ArgumentParser(description="Export browser cookies to Netscape format")
    parser.add_argument("--browser", required=True, choices=["chrome", "chromium", "brave", "firefox"])
    parser.add_argument("--domain", required=True, help="Domain to export, e.g. youtube.com")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()

    return export_cookies(args.browser, args.domain, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
