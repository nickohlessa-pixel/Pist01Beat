"""
pist01beat.ops.export_cli

One-command audited export runner:
model_export -> validate -> hash -> stamp (diff_summary optional)

Infrastructure-only. Best-effort imports. Deterministic JSON writing.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Optional


EXPORT_CLI_VERSION = "export_cli_v1_readonly"
# best-effort repo guard (warnings only)
try:
    from pist01beat.ops.repo_guard import detect_repo_root as _detect_repo_root  # type: ignore
except Exception:
    _detect_repo_root = None


def _json_dumps_deterministic(obj: Any) -> str:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _safe_read_json(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _call_best_effort(func, *arg_sets):
    """
    Try calling func with multiple arg tuples until one works.
    """
    last_err = None
    for args in arg_sets:
        try:
            return func(*args)
        except Exception as e:
            last_err = e
            continue
    raise last_err  # type: ignore[misc]


def build_audited_export() -> dict:
    """
    Returns:
    {
      "export": <raw export dict>,
      "validation": {ok, errors, warnings},
      "export_hash": <sha256 string or None>,
      "stamp": <stamp dict or None>,
      "cli_warnings": [..],
      "version": <EXPORT_CLI_VERSION>
    }
    Best-effort: missing helpers degrade to None + warnings.
    Deterministic: stable key ordering when serialized.
    """
    cli_warnings: List[str] = []

    # Preflight: repo layout guard (non-fatal, warnings only)
    if _detect_repo_root is None:
        cli_warnings.append("repo_guard_missing")
    else:
        try:
            info = _detect_repo_root(".")
            w = info.get("warnings") if isinstance(info, dict) else None
            if isinstance(w, list) and len(w) > 0:
                cli_warnings.append("repo_layout_invalid")
        except Exception:
            cli_warnings.append("repo_layout_invalid")

    build_model_export = None
    validate_export = None
    hash_export = None
    stamp_export = None

    # Best-effort imports (graceful)
    try:
        from pist01beat.ops.model_export import build_model_export as _bme  # type: ignore
        build_model_export = _bme
    except Exception:
        cli_warnings.append("missing_model_export")

    try:
        from pist01beat.ops.export_validate import validate_export as _ve  # type: ignore
        validate_export = _ve
    except Exception:
        cli_warnings.append("missing_export_validate")

    try:
        from pist01beat.ops.export_hash import hash_export as _he  # type: ignore
        hash_export = _he
    except Exception:
        cli_warnings.append("missing_export_hash")

    try:
        from pist01beat.ops.export_stamp import stamp_export as _se  # type: ignore
        stamp_export = _se
    except Exception:
        cli_warnings.append("missing_export_stamp")

    export_obj: Optional[Dict[str, Any]] = None
    validation_obj: Optional[Dict[str, Any]] = None
    export_hash: Optional[str] = None
    stamp_obj: Optional[Dict[str, Any]] = None

    # Build export
    if build_model_export is not None:
        try:
            export_obj = build_model_export()
        except Exception:
            export_obj = None
            cli_warnings.append("model_export_failed")

    # Validate
    if validate_export is not None and export_obj is not None:
        try:
            v = _call_best_effort(
                validate_export,
                (export_obj,),
            )
            # Normalize to dict {ok, errors, warnings}
            if isinstance(v, dict):
                validation_obj = {
                    "ok": bool(v.get("ok", False)),
                    "errors": v.get("errors", []) or [],
                    "warnings": v.get("warnings", []) or [],
                }
            else:
                # unknown shape, preserve safely
                validation_obj = {"ok": False, "errors": ["validate_export_return_shape"], "warnings": []}
                cli_warnings.append("validate_export_return_shape")
        except Exception:
            validation_obj = {"ok": False, "errors": ["validate_export_failed"], "warnings": []}
            cli_warnings.append("validate_export_failed")
    else:
        validation_obj = None

    # Hash
    if hash_export is not None and export_obj is not None:
        try:
            h = _call_best_effort(
                hash_export,
                (export_obj,),
            )
            export_hash = str(h) if h is not None else None
        except Exception:
            export_hash = None
            cli_warnings.append("hash_export_failed")

    # Stamp
    if stamp_export is not None and export_obj is not None:
        try:
            # try a few common signatures
            s = _call_best_effort(
                stamp_export,
                (export_obj, export_hash),
                (export_obj,),
            )
            stamp_obj = s if isinstance(s, dict) else None
            if stamp_obj is None:
                cli_warnings.append("stamp_export_return_shape")
        except Exception:
            stamp_obj = None
            cli_warnings.append("stamp_export_failed")

    # Fixed top-level key set + deterministic insertion order
    out: Dict[str, Any] = {}
    out["export"] = export_obj
    out["validation"] = validation_obj
    out["export_hash"] = export_hash
    out["stamp"] = stamp_obj
    out["cli_warnings"] = cli_warnings
    out["version"] = EXPORT_CLI_VERSION
    return out


def _short_summary(bundle: dict) -> str:
    export_obj = bundle.get("export") or {}
    validation = bundle.get("validation") or {}
    ok = validation.get("ok", None)
    errors = validation.get("errors") or []
    warnings = validation.get("warnings") or []
    h = bundle.get("export_hash") or ""
    stamp = bundle.get("stamp") or {}
    cli_w = bundle.get("cli_warnings") or []

    export_version = export_obj.get("version") if isinstance(export_obj, dict) else None

    summary = {
        "cli_version": bundle.get("version"),
        "export_version": export_version,
        "validation_ok": ok,
        "errors_n": len(errors) if isinstance(errors, list) else None,
        "warnings_n": len(warnings) if isinstance(warnings, list) else None,
        "hash_prefix": h[:12] if isinstance(h, str) else None,
        "stamp_keys": sorted(list(stamp.keys())) if isinstance(stamp, dict) else None,
        "cli_warnings_n": len(cli_w) if isinstance(cli_w, list) else None,
    }
    return _json_dumps_deterministic(summary)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="export_cli", add_help=True)
    p.add_argument("--write", type=str, default=None, help="Write audited bundle JSON to this path (deterministic).")
    p.add_argument("--print", dest="do_print", action="store_true", help="Print a short deterministic summary.")
    args = p.parse_args(argv)

    bundle = build_audited_export()

    if args.do_print:
        print(_short_summary(bundle))

    if args.write:
        # Write stamped audited bundle (deterministic JSON)
        payload = _json_dumps_deterministic(bundle)
        with open(args.write, "w", encoding="utf-8") as f:
            f.write(payload + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
