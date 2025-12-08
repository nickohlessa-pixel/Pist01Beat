# FILE: identity_engine.py
"""
Identity Engine for Pist01 Beat v3.4.

This module converts team identity profiles into base spread and base total
projections using only configuration data and simple, deterministic math.

It is intentionally lightweight:
- pulls team profiles and baselines from config.py
- computes power/pace/offense/defense driven base projections
- returns a structured identity dict for consumption by other engines
"""

from typing import Any, Dict
import math

import load_config  # noqa: F401 (imported for side-effects / future use)

from config import TEAM_PROFILES, SPREAD_TOTAL_BASELINES, MODEL_VERSION

# Try to import engine-specific errors; provide local fallbacks if unavailable.
try:
    from errors import TeamProfileError, CalculationError  # type: ignore
except Exception:  # pragma: no cover

    class TeamProfileError(Exception):
        """Raised when a team profile is missing or malformed."""

    class CalculationError(Exception):
        """Raised when identity calculations cannot be completed."""


def _coerce_float(value: Any, context: str) -> float:
    """
    Best-effort conversion of a value to float with clear error context.
    """
    try:
        return float(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise CalculationError(f"Unable to convert value to float in {context}: {value!r}") from exc


def get_team_profile(team_code: str) -> Dict[str, float]:
    """
    Normalize a team code, look up its profile from TEAM_PROFILES,
    and fall back to the 'GENERIC' profile if the code is unknown.

    Required numeric keys:
        - base_power
        - offense
        - defense
        - pace
        - chaos
        - volatility

    Raises:
        TeamProfileError: if TEAM_PROFILES is missing or malformed,
                          or if the GENERIC profile is missing/invalid
                          when needed.
    """
    if not isinstance(TEAM_PROFILES, dict):
        raise TeamProfileError("TEAM_PROFILES must be a dict in config.py")

    normalized_code = (team_code or "").strip().upper()
    if not normalized_code:
        normalized_code = "GENERIC"

    if normalized_code in TEAM_PROFILES:
        raw_profile = TEAM_PROFILES[normalized_code]
        source_code = normalized_code
    else:
        # Fallback to GENERIC if available
        if "GENERIC" not in TEAM_PROFILES:
            raise TeamProfileError(
                f"Unknown team code '{normalized_code}' and no GENERIC profile defined."
            )
        raw_profile = TEAM_PROFILES["GENERIC"]
        source_code = "GENERIC"

    if not isinstance(raw_profile, dict):
        raise TeamProfileError(
            f"Profile for '{source_code}' must be a dict, got {type(raw_profile).__name__}"
        )

    required_keys = ["base_power", "offense", "defense", "pace", "chaos", "volatility"]

    # Validate required keys exist
    missing = [key for key in required_keys if key not in raw_profile]
    if missing:
        raise TeamProfileError(
            f"Profile for '{source_code}' is missing required keys: {', '.join(missing)}"
        )

    # Build a normalized numeric profile
    profile: Dict[str, float] = {}
    for key in required_keys:
        profile[key] = _coerce_float(raw_profile[key], f"profile[{source_code}].{key}")

    # Optionally carry through any additional numeric fields (non-required)
    for key, value in raw_profile.items():
        if key in required_keys:
            continue
        if isinstance(value, (int, float)):
            profile[key] = float(value)

    return profile


class IdentityEngine:
    """
    Identity Engine v3.4

    Responsible for:
    - Turning team profiles into a base matchup identity
    - Producing base spread and base total BEFORE chaos/volatility adjustments
    """

    def __init__(self, model_version: str | None = None) -> None:
        """
        Initialize the Identity Engine.

        Args:
            model_version: Optional explicit version string. If None, defaults
                           to MODEL_VERSION from config.py.
        """
        # Store version string
        self.version: str = model_version or str(MODEL_VERSION)

        # Optionally trigger config validation/loading side effects.
        # We do not assume a specific API from load_config; importing it
        # at module level is enough for most patterns used in this project.

    def _get_baseline(self, key: str) -> float:
        """
        Fetch and coerce a baseline value from SPREAD_TOTAL_BASELINES.

        Raises:
            CalculationError: if the key is missing or not convertible.
        """
        if not isinstance(SPREAD_TOTAL_BASELINES, dict):
            raise CalculationError("SPREAD_TOTAL_BASELINES must be a dict in config.py")

        if key not in SPREAD_TOTAL_BASELINES:
            raise CalculationError(
                f"Missing baseline key '{key}' in SPREAD_TOTAL_BASELINES."
            )

        return _coerce_float(SPREAD_TOTAL_BASELINES[key], f"SPREAD_TOTAL_BASELINES[{key}]")

    def compute_identity(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """
        Compute the base identity matchup between two teams.

        Returns a dict containing at least:
            - "engine_version"
            - "home_team"
            - "away_team"
            - "base_spread" (float)
            - "base_total" (float)
            - "pace_factor" (float)
            - "power_diff" (float)
            - "notes" (str)
            - "debug" (dict with inputs and intermediate calculations)

        Raises:
            TeamProfileError: for missing/malformed team profiles.
            CalculationError: for missing baselines or numeric issues.
        """
        home_code = (home_team or "").strip().upper()
        away_code = (away_team or "").strip().upper()

        # Fetch and validate team profiles
        home_profile = get_team_profile(home_code)
        away_profile = get_team_profile(away_code)

        # Pull required baselines
        default_total = self._get_baseline("default_total")
        home_edge = self._get_baseline("home_edge")
        pace_spread_scale = self._get_baseline("pace_spread_scale")
        pace_total_scale = self._get_baseline("pace_total_scale")
        power_spread_scale = self._get_baseline("power_spread_scale")

        # Core identity metrics
        power_diff = home_profile["base_power"] - away_profile["base_power"]
        pace_factor = (home_profile["pace"] + away_profile["pace"]) / 2.0
        off_factor = (home_profile["offense"] + away_profile["offense"]) / 2.0
        def_factor = (home_profile["defense"] + away_profile["defense"]) / 2.0

        # Base spread:
        #   - home_edge gives generic home-court advantage
        #   - power_diff tilts the spread toward the stronger power rating
        #   - pace_factor provides a small tweak (in faster games, edges can grow a bit)
        pace_spread_adjust = pace_spread_scale * (pace_factor - 1.0)
        base_spread = home_edge + power_spread_scale * power_diff + pace_spread_adjust

        # Base total:
        #   - anchored at default_total
        #   - scaled by pace (faster games → higher totals)
        #   - nudged by offense/defense balance
        pace_total_adjust = pace_total_scale * (pace_factor - 1.0)

        # Small offense/defense influence:
        # Higher offense and weaker defense → slightly higher total.
        off_def_delta = off_factor - def_factor
        # Keep this intentionally modest; scale it down.
        off_def_adjust_scale = 0.5
        off_def_adjust = off_def_delta * off_def_adjust_scale

        base_total = default_total + pace_total_adjust + off_def_adjust

        # Ensure numeric cleanliness (e.g., avoid -0.0)
        base_spread = float(round(base_spread, 3))
        base_total = float(round(base_total, 3))
        pace_factor_out = float(round(pace_factor, 3))
        power_diff_out = float(round(power_diff, 3))
        off_factor_out = float(round(off_factor, 3))
        def_factor_out = float(round(def_factor, 3))

        result: Dict[str, Any] = {
            "engine_version": self.version,
            "home_team": home_code,
            "away_team": away_code,
            "base_spread": base_spread,
            "base_total": base_total,
            "pace_factor": pace_factor_out,
            "power_diff": power_diff_out,
            "notes": "Identity Engine v3.4 base matchup identity.",
            "debug": {
                "home_profile": home_profile,
                "away_profile": away_profile,
                "baselines": {
                    "default_total": default_total,
                    "home_edge": home_edge,
                    "pace_spread_scale": pace_spread_scale,
                    "pace_total_scale": pace_total_scale,
                    "power_spread_scale": power_spread_scale,
                },
                "intermediate": {
                    "power_diff": power_diff_out,
                    "pace_factor": pace_factor_out,
                    "off_factor": off_factor_out,
                    "def_factor": def_factor_out,
                    "pace_spread_adjust": pace_spread_adjust,
                    "pace_total_adjust": pace_total_adjust,
                    "off_def_adjust": off_def_adjust,
                    "off_def_delta": off_def_delta,
                },
            },
        }

        return result


def compute_identity_matchup(home_team: str, away_team: str) -> Dict[str, Any]:
    """
    Convenience wrapper that instantiates IdentityEngine and calls compute_identity.
    """
    engine = IdentityEngine()
    return engine.compute_identity(home_team, away_team)


if __name__ == "__main__":
    sample = compute_identity_matchup("HOR", "DEN")
    print("✅ IdentityEngine self-test result:")
    print(sample)
