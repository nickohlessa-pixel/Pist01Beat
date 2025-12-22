
"""
CLI wrapper for ops_index registry (read-only).

Prints:
- default: one-line OK tools:<n> warnings:<n>
- --json: full JSON
"""

from __future__ import annotations

import argparse
import json
from typing import List, Optional

from pist01beat.ops.ops_index import build_ops_index

OPS_INDEX_CLI_VERSION = "ops_index_cli_v1_readonly"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ops_index_cli",
        description="Read-only ops tool index registry.",
    )
    p.add_argument("--json", action="store_true", help="Print full JSON (default prints one-line summary).")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON (only with --json).")
    p.add_argument("--version", action="store_true", help="Print CLI version and exit.")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(OPS_INDEX_CLI_VERSION)
        return 0

    idx = build_ops_index()

    if args.json:
        if args.pretty:
            print(json.dumps(idx, sort_keys=True, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(idx, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        return 0

    n_tools = len(idx.get("tools", []) or [])
    n_warn = len(idx.get("warnings", []) or [])
    print(f"OK tools:{n_tools} warnings:{n_warn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
