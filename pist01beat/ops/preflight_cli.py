
"""
Read-only preflight CLI.

Purpose:
- One-command sanity check for fresh clones / environment drift
- Deterministic, minimal, infrastructure-only output
- Zero model authority, zero engine imports

Outputs:
- python version
- pist01beat package location
- repo root (as detected by repo_snapshot)
- repo fingerprint (sha256, first 12 chars in summary)
- file count, warnings count
- git HEAD (best-effort; warn-only if unavailable)

No writes. Prints to stdout only.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from typing import Dict, List, Optional

import pist01beat
from pist01beat.ops.repo_snapshot import build_repo_snapshot

PREFLIGHT_CLI_VERSION = "preflight_cli_v1_readonly"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="preflight_cli",
        description="Read-only preflight: environment + repo fingerprint (deterministic).",
    )
    p.add_argument("--repo-root", default=None, help="Repo root path. Default: auto-detect from CWD.")
    p.add_argument("--max-file-mb", type=int, default=25, help="Skip files larger than this size (MB). Default: 25.")
    p.add_argument("--follow-symlinks", action="store_true", help="Follow symlinks during walk (default: false).")
    p.add_argument("--exclude-dir", action="append", default=[], help="Additional dir basename excludes (repeatable).")
    p.add_argument("--exclude-file", action="append", default=[], help="Additional file basename excludes (repeatable).")
    p.add_argument("--json", action="store_true", help="Print full JSON report (default prints one-line summary).")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON (only with --json).")
    p.add_argument("--version", action="store_true", help="Print CLI version and exit.")
    return p


def _best_effort_git_head() -> Dict[str, Optional[str]]:
    """
    Read-only git head info.
    Warn-only behavior. Returns dict with:
      - git_head: str|None
      - git_is_dirty: bool|None
      - git_error: str|None
    """
    out: Dict[str, Optional[str]] = {"git_head": None, "git_is_dirty": None, "git_error": None}
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        out["git_head"] = head
    except Exception as e:
        out["git_error"] = f"git_head_unavailable: {type(e).__name__}"
        return out

    try:
        status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
        out["git_is_dirty"] = bool(status.strip())
    except Exception as e:
        # Don't fail preflight if status fails
        out["git_error"] = f"git_status_unavailable: {type(e).__name__}"
    return out


def build_preflight_report(
    repo_root: Optional[str],
    max_file_mb: int,
    follow_symlinks: bool,
    exclude_dir: Optional[List[str]],
    exclude_file: Optional[List[str]],
) -> Dict:
    warnings: List[str] = []

    # Repo snapshot (deterministic fingerprint; excludes created_at_utc from fingerprint by design)
    snap = build_repo_snapshot(
        repo_root=repo_root,
        excluded_dirs=exclude_dir if exclude_dir else None,
        excluded_files=exclude_file if exclude_file else None,
        max_file_mb=max_file_mb,
        follow_symlinks=follow_symlinks,
    )

    git_info = _best_effort_git_head()
    if git_info.get("git_error"):
        warnings.append(git_info["git_error"])

    # Environment
    py_ver = sys.version.splitlines()[0]
    plat = platform.platform()

    report: Dict = {
        "version": PREFLIGHT_CLI_VERSION,
        "python_version": py_ver,
        "platform": plat,
        "pist01beat_file": getattr(pist01beat, "__file__", None),
        "repo_root": snap.get("repo_root"),
        "repo_fingerprint_sha256": snap.get("repo_fingerprint_sha256"),
        "repo_files_count": len(snap.get("files", []) or []),
        "repo_warnings_count": len(snap.get("warnings", []) or []),
        "snapshot_warnings": snap.get("warnings", []) or [],
        "git_head": git_info.get("git_head"),
        "git_is_dirty": git_info.get("git_is_dirty"),
        "warnings": warnings,
    }
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(PREFLIGHT_CLI_VERSION)
        return 0

    report = build_preflight_report(
        repo_root=args.repo_root,
        max_file_mb=int(args.max_file_mb),
        follow_symlinks=bool(args.follow_symlinks),
        exclude_dir=args.exclude_dir if args.exclude_dir else None,
        exclude_file=args.exclude_file if args.exclude_file else None,
    )

    if args.json:
        if args.pretty:
            print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        return 0

    # Default: one-line summary
    fp12 = (report.get("repo_fingerprint_sha256") or "")[:12]
    n_files = int(report.get("repo_files_count") or 0)
    snap_warns = int(report.get("repo_warnings_count") or 0)
    local_warns = len(report.get("warnings", []) or [])
    git_head = (report.get("git_head") or "")[:12] if report.get("git_head") else "nogit"

    dirty = report.get("git_is_dirty")
    dirty_s = "dirty" if dirty else ("clean" if dirty is False else "unknown")

    print(f"OK fp:{fp12} files:{n_files} snap_warn:{snap_warns} warn:{local_warns} git:{git_head} {dirty_s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
