
"""
Deterministic, read-only repo snapshot manifest.

- No side effects on import
- No writes by default
- Stable ordering
- Streamed sha256 hashing
- Deterministic repo fingerprint (excludes created_at_utc)
"""

from __future__ import annotations

import datetime as _dt
import hashlib as _hashlib
import json as _json
import os as _os
from pathlib import Path as _Path
from typing import Dict, List, Optional, Set, Tuple

REPO_SNAPSHOT_VERSION = "repo_snapshot_v1_readonly"


def _utc_now_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_normalize(obj: dict) -> str:
    return _json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_file(path: _Path, chunk_bytes: int = 1024 * 1024) -> str:
    h = _hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk_bytes)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _find_repo_root(start: _Path) -> Tuple[_Path, List[str]]:
    warnings: List[str] = []
    cur = start.resolve()
    for _ in range(40):
        if (cur / ".git").exists() or (cur / "pyproject.toml").exists() or (cur / "setup.cfg").exists() or (cur / "requirements.txt").exists():
            return cur, warnings
        if cur.parent == cur:
            break
        cur = cur.parent
    warnings.append("repo_root_not_detected: falling back to provided start path")
    return start.resolve(), warnings


def build_repo_snapshot(
    repo_root: Optional[str] = None,
    excluded_dirs: Optional[List[str]] = None,
    excluded_files: Optional[List[str]] = None,
    max_file_mb: int = 25,
    follow_symlinks: bool = False,
) -> Dict:
    warnings: List[str] = []

    start = _Path(repo_root).expanduser().resolve() if repo_root else _Path.cwd().resolve()
    root, root_warnings = _find_repo_root(start)
    warnings.extend(root_warnings)

    default_ex_dirs = [".git", "__pycache__", ".ipynb_checkpoints", "exports"]
    default_ex_files: List[str] = []

    ex_dirs: Set[str] = set(default_ex_dirs)
    ex_files: Set[str] = set(default_ex_files)

    if excluded_dirs:
        ex_dirs.update(excluded_dirs)
    if excluded_files:
        ex_files.update(excluded_files)

    max_bytes = int(max_file_mb) * 1024 * 1024

    file_rows: List[Dict] = []
    skipped_files: List[str] = []
    skipped_dirs: List[str] = []

    for dirpath, dirnames, filenames in _os.walk(root, topdown=True, followlinks=follow_symlinks):
        dirpath_p = _Path(dirpath)

        kept_dirs: List[str] = []
        for d in dirnames:
            if d in ex_dirs:
                skipped_dirs.append((dirpath_p / d).relative_to(root).as_posix())
            else:
                kept_dirs.append(d)
        dirnames[:] = sorted(kept_dirs)

        for fn in sorted(filenames):
            if fn in ex_files:
                skipped_files.append((dirpath_p / fn).relative_to(root).as_posix())
                continue

            full = dirpath_p / fn

            if full.is_symlink() and not follow_symlinks:
                relp = full.relative_to(root).as_posix()
                skipped_files.append(relp)
                warnings.append(f"skipped_symlink: {relp}")
                continue

            if not full.is_file():
                skipped_files.append(full.relative_to(root).as_posix())
                continue

            size_bytes = int(full.stat().st_size)
            if size_bytes > max_bytes:
                relp = full.relative_to(root).as_posix()
                skipped_files.append(relp)
                warnings.append(f"skipped_huge_file: {relp}")
                continue

            sha = _sha256_file(full)
            file_rows.append({"path": full.relative_to(root).as_posix(), "size_bytes": size_bytes, "sha256": sha})

    file_rows.sort(key=lambda r: r["path"])

    snapshot: Dict = {
        "version": REPO_SNAPSHOT_VERSION,
        "repo_root": root.as_posix(),
        "created_at_utc": _utc_now_iso(),
        "excluded_dirs": sorted(ex_dirs),
        "excluded_files": sorted(ex_files),
        "warnings": warnings,
        "files": file_rows,
    }

    fingerprint_payload = dict(snapshot)
    fingerprint_payload.pop("created_at_utc", None)

    normalized = _json_normalize(fingerprint_payload)
    snapshot["repo_fingerprint_sha256"] = _hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    snapshot["excluded_dirs_detected"] = sorted(set(skipped_dirs))
    snapshot["excluded_files_detected"] = sorted(set(skipped_files))

    return snapshot
