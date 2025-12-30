import csv
from datetime import datetime
from math import isfinite
from typing import Dict, List, Any

VALID_SPREAD_RESULTS = {"covered", "not", "push"}
VALID_TOTAL_RESULTS = {"over", "under", "push"}

REQUIRED_COLUMNS = [
    "Date",
    "Away Team",
    "Home Team",
    "Closing Spread",
    "Closing Total",
    "Away Score",
    "Home Score",
    "Spread Result",
    "Total Result",
]


def normalize_date(date_str: str) -> str:
    s = (date_str or "").strip()
    if not s:
        raise ValueError("Date is empty")

    formats = ["%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    raise ValueError(f"Invalid date format: {date_str}")


def parse_spread(spread_str: str) -> float:
    s = (spread_str or "").strip()
    if not s:
        raise ValueError("Closing Spread is empty")

    parts = s.split()
    if len(parts) != 2:
        raise ValueError(f"Invalid spread format: {spread_str}")

    value = float(parts[1])
    if not isfinite(value):
        raise ValueError(f"Non-finite spread value: {value}")

    return value


def _require_columns(fieldnames: List[str]) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in (fieldnames or [])]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _clean_str(v: Any, label: str) -> str:
    s = ("" if v is None else str(v)).strip()
    if not s:
        raise ValueError(f"{label} is empty")
    return s


def _parse_int(v: Any, label: str) -> int:
    n = int(_clean_str(v, label))
    if n < 0:
        raise ValueError(f"{label} must be >= 0: {n}")
    return n


def _parse_float(v: Any, label: str) -> float:
    x = float(_clean_str(v, label))
    if not isfinite(x):
        raise ValueError(f"{label} must be finite: {x}")
    return x


def load_market_log(csv_path: str) -> List[Dict[str, Any]]:
    normalized_rows: List[Dict[str, Any]] = []

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        _require_columns(reader.fieldnames or [])

        for i, row in enumerate(reader, start=1):
            try:
                normalized = {
                    "date": normalize_date(row.get("Date")),
                    "away_team": _clean_str(row.get("Away Team"), "Away Team"),
                    "home_team": _clean_str(row.get("Home Team"), "Home Team"),
                    "home_spread": parse_spread(row.get("Closing Spread")),
                    "closing_total": _parse_float(row.get("Closing Total"), "Closing Total"),
                    "away_score": _parse_int(row.get("Away Score"), "Away Score"),
                    "home_score": _parse_int(row.get("Home Score"), "Home Score"),
                    "spread_result": _clean_str(row.get("Spread Result"), "Spread Result").lower(),
                    "total_result": _clean_str(row.get("Total Result"), "Total Result").lower(),
                }

                if normalized["spread_result"] not in VALID_SPREAD_RESULTS:
                    raise ValueError(f"Invalid spread_result: {normalized['spread_result']}")
                if normalized["total_result"] not in VALID_TOTAL_RESULTS:
                    raise ValueError(f"Invalid total_result: {normalized['total_result']}")

                normalized_rows.append(normalized)

            except Exception as e:
                raise ValueError(f"Row {i} failed validation: {e}") from None

    return normalized_rows
