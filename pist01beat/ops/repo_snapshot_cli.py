
"""
CLI wrapper for deterministic repo snapshot manifest.

- Read-only
- No side effects on import
- Prints to stdout only (caller decides what to do with it)
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from pist01beat.ops.repo_snapshot import build_repo_snapshot

REPO_SNAPSHOT_CLI_VERSION = "repo_snapshot_cli_v1_readonly"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="repo_snapshot_cli",
        description="Read-only deterministic repo snapshot manifest + fingerprint.",
    )
    p.add_argument("--repo-root", default=None, help="Repo root path. Default: auto-detect from CWD.")
    p.add_argument("--max-file-mb", type=int, default=25, help="Skip files larger than this size (MB). Default: 25.")
    p.add_argument("--follow-symlinks", action="store_true", help="Follow symlinks during walk (default: false).")

    p.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Additional directory basename to exclude (repeatable). Example: --exclude-dir build",
    )
    p.add_argument(
        "--exclude-file",
        action="append",
        default=[],
        help="Additional file basename to exclude (repeatable). Example: --exclude-file secrets.txt",
    )

    p.add_argument(
        "--json",
        action="store_true",
        help="Print full snapshot JSON (default prints a one-line summary).",
    )
    p.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON (only applies with --json).",
    )
    p.add_argument(
        "--version",
        action="store_true",
        help="Print CLI version and exit.",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(REPO_SNAPSHOT_CLI_VERSION)
        return 0

    snapshot = build_repo_snapshot(
        repo_root=args.repo_root,
        excluded_dirs=args.exclude_dir if args.exclude_dir else None,
        excluded_files=args.exclude_file if args.exclude_file else None,
        max_file_mb=args.max_file_mb,
        follow_symlinks=bool(args.follow_symlinks),
    )

    if args.json:
        if args.pretty:
            print(json.dumps(snapshot, sort_keys=True, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        return 0

    # Default: minimal stdout (fingerprint + file count + warnings count)
    fp = snapshot.get("repo_fingerprint_sha256", "")[:12]
    n_files = len(snapshot.get("files", []))
    n_warn = len(snapshot.get("warnings", []) or [])
    print(f"OK {fp} files:{n_files} warnings:{n_warn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
