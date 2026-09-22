# Privacy and safe publishing

Do not commit cookies, authentication tokens, private keys, signed URL lists,
private media, environment files, or personal directory layouts. Example commands
use relative paths. `VD_CONFIG_DIR`, `VD_LOGS_DIR`, and executable overrides keep
local configuration separate from public source.

Cookie export validates a hostname before opening a browser, filters cookies on
DNS boundaries, rejects control characters and output symlinks, and atomically
writes owner-only files on POSIX. New export directories request mode 0700.
Existing directory permissions are not changed. Windows ACL hardening is not
implemented or tested; handle exported cookies as credentials on every platform.

Human-readable CLI downloader output and GUI logs mask URL paths, user information,
queries, and fragments. Logging also replaces known local project/config/log/home
roots. Execution URLs remain unchanged. Redaction is conservative and can remove
useful diagnostic detail; it does not promise to discover every arbitrary secret,
private filename, or third-party output format. Review logs before sharing.

Use `./scripts/vd doctor --json --redact` for diagnostics without executable paths.
The ordinary doctor report is intended for local use and includes tool locations.
The Chrome extension must preserve actual captured URLs for downloads to work;
its exported lists are sensitive and are not covered by terminal-log redaction.
No private browser databases or real cookie values are needed by the tests.

Before publishing, stage only intended files, then run:

```bash
python3 scripts/check_public_tree.py
```

The guard inspects the Git index for personal absolute paths and private-key
markers and reports only the relative source file and rule, never matched values.
It complements Gitleaks, which checks a tracked snapshot and reachable Git history.
No scanner proves that all secrets are absent. If a real secret was previously
published, revoke/rotate it; deleting a working-tree file does not remove history.
