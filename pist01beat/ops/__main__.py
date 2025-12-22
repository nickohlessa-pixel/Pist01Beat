
"""
pist01beat.ops module dispatcher.

Usage:
  python -m pist01beat.ops <command> [args...]

Commands (read-only tooling):
  preflight        -> pist01beat.ops.preflight_cli
  repo-snapshot    -> pist01beat.ops.repo_snapshot_cli

Design:
- No side effects on import
- No writes
- Minimal dependencies
- Delegates to each CLI's main(argv)
"""

from __future__ import annotations

import sys
from typing import List

OPS_DISPATCH_VERSION = "ops_dispatch_v1_readonly"


def _print_help() -> None:
    msg = f"""pist01beat.ops ({OPS_DISPATCH_VERSION})

Usage:
  python -m pist01beat.ops <command> [args...]

Commands:
  preflight
  index
    Run read-only environment + repo fingerprint preflight.

  repo-snapshot
    Run read-only repo snapshot/fingerprint tool.

Examples:
  python -m pist01beat.ops preflight
  python -m pist01beat.ops preflight --json --pretty
  python -m pist01beat.ops repo-snapshot
  python -m pist01beat.ops repo-snapshot --json --pretty
  python -m pist01beat.ops index
  python -m pist01beat.ops index --json --pretty

Notes:
  - This dispatcher is infrastructure-only and read-only.
  - It delegates to underlying CLI modules.
"""
    print(msg)


def main(argv: List[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        _print_help()
        return 0

    cmd = args[0]
    sub_argv = args[1:]

    if cmd == "preflight":
        from pist01beat.ops.preflight_cli import main as _preflight_main
        return int(_preflight_main(sub_argv))

    if cmd in ("repo-snapshot", "repo_snapshot"):
        from pist01beat.ops.repo_snapshot_cli import main as _snap_main
        return int(_snap_main(sub_argv))

    if cmd == "index":
        from pist01beat.ops.ops_index_cli import main as _index_main
        return int(_index_main(sub_argv))

    if cmd == "version":
        print(OPS_DISPATCH_VERSION)
        return 0

    print(f"Unknown command: {cmd}\n")
    _print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
