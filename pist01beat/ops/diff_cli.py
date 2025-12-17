"""
pist01beat.ops.diff_cli

CLI wrapper for export_diff + diff_summary (best-effort).
Infrastructure-only. Deterministic output. No engine imports.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Optional


DIFF_CLI_VERSION = "diff_cli_v1_readonly"


def _json_dumps_deterministic(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _read_json(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def diff_exports(a_path: str, b_path: str) -> dict:
    """
    Returns fixed keys:
    {
      "a_path": str,
      "b_path": str,
      "ok": bool,
      "diff": <dict or None>,
      "summary": <dict or None>,
      "warnings": [..],
      "version": <DIFF_CLI_VERSION>
    }
    """
    warnings: List[str] = []

    export_diff = None
    diff_summary = None

    try:
        from pist01beat.ops.export_diff import diff_exports as _de  # type: ignore
        export_diff = _de
    except Exception:
        warnings.append("missing_export_diff")

    try:
        from pist01beat.ops.diff_summary import summarize_diff as _sd  # type: ignore
        diff_summary = _sd
    except Exception:
        warnings.append("missing_diff_summary")

    a = _read_json(a_path)
    b = _read_json(b_path)

    out: Dict[str, Any] = {}
    out["a_path"] = a_path
    out["b_path"] = b_path
    out["ok"] = False
    out["diff"] = None
    out["summary"] = None
    out["warnings"] = warnings
    out["version"] = DIFF_CLI_VERSION

    if a is None:
        warnings.append("read_failed_a")
        return out
    if b is None:
        warnings.append("read_failed_b")
        return out

    if export_diff is None:
        warnings.append("diff_failed_missing_export_diff")
        return out

    try:
        d = export_diff(a, b)
        out["diff"] = d
    except Exception:
        warnings.append("export_diff_failed")
        return out

    if diff_summary is not None and out["diff"] is not None:
        try:
            s = diff_summary(out["diff"])
            out["summary"] = s if isinstance(s, dict) else None
            if out["summary"] is None:
                warnings.append("diff_summary_return_shape")
        except Exception:
            warnings.append("diff_summary_failed")

    out["ok"] = True
    return out


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="diff_cli", add_help=True)
    p.add_argument("--a", required=True, help="Path to export A JSON")
    p.add_argument("--b", required=True, help="Path to export B JSON")
    p.add_argument("--write", default=None, help="Write full diff bundle JSON to this path (deterministic).")
    p.add_argument("--print", dest="do_print", action="store_true", help="Print deterministic short summary JSON.")
    args = p.parse_args(argv)

    res = diff_exports(args.a, args.b)

    if args.do_print:
        short = {
            "ok": res.get("ok"),
            "warnings_n": len(res.get("warnings") or []),
            "has_summary": bool(res.get("summary")),
            "has_diff": bool(res.get("diff")),
            "version": res.get("version"),
        }
        print(_json_dumps_deterministic(short))

    if args.write:
        payload = _json_dumps_deterministic(res)
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(payload + "\n")

    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
