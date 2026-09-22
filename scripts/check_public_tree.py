#!/usr/bin/env python3
"""Reject accidentally staged host-specific paths without displaying their values.

This complements a secret scanner; it is not a universal privacy detector.
Inspect the Git index, not untracked local configuration or browser profiles.
"""
from __future__ import annotations

import re
import subprocess


def main() -> int:
    names = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
    rules = {
        'personal absolute path': re.compile(r'/(?:home|Users)/[A-Za-z0-9_.-]+/|[A-Z]:\\(?:Users|Projects)\\'),
        'private key file': re.compile(r'-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----'),
    }
    failures = []
    for name in filter(None, names):
        content = subprocess.check_output(['git', 'show', ':' + name]).decode('utf-8', errors='replace')
        for label, pattern in rules.items():
            if pattern.search(content):
                failures.append((name, label))
    for name, label in failures:
        print(f'{name}: {label} detected (value withheld)')
    print(f'Public-tree check: {len(failures)} finding(s). Also run Gitleaks.')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
