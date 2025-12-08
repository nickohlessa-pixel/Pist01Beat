# FILE: volatility_engine.py
"""
Volatility Engine for Pist01 Beat v3.4.

This module converts team identity profiles into a matchup-level volatility
score and volatility flag using only configuration data and simple,
deterministic math.

It is intentionally lightweight:
- pulls team profiles and volatility baselines from config.py
- uses chaos, volatility, and pace traits to derive a volatility_score
- returns a structured dict for consumption by other engines
"""

from typing import Any, Dict
import math

import load_config  # noqa: F401 (imported for side-effects / future use)

from config import TEAM_PROFILES, MODEL_VERSION, VOLATILITY_BASELINES

# Try to import engine-specific errors; provide local fallbacks if unavailable.
try:
    from errors import TeamProfileError, CalculationError  # type: ignore
except Exception:  # pragma: no cover

    class TeamProfileError(Exception):
        """Raised when a team profile is missing or malformed."""

    class CalculationError(Exception):
        """Raised when volatility calculations cannot be completed."""


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


class VolatilityEngine:
    """
    Volatility Engine v3.4

    Responsible for:
    - Turning team volatility/chaos/pace identity into a matchup-level volatility signal
    - Producing a volatility_score and volatility_flag BEFORE other adjustments
    """

    def __init__(self, model_version: str | None = None) -> None:
        """
        Initialize the Volatility Engine.

        Args:
            model_version: Optional explicit version string. If None, defaults
                           to MODEL_VERSION from config.py.
        """
        self.version: str = model_version or str(MODEL_VERSION)

    def _get_baseline(self, key: str) -> float:
        """
        Fetch and coerce a baseline value from VOLATILITY_BASELINES.

        Raises:
            CalculationError: if the key is missing or not convertible.
        """
        if not isinstance(VOLATILITY_BASELINES, dict):
            raise CalculationError("VOLATILITY_BASELINES must be a dict in config.py")

        if key not in VOLATILITY_BASELINES:
            raise CalculationError(
                f"Missing baseline key '{key}' in VOLATILITY_BASELINES."
            )

        return _coerce_float(VOLATILITY_BASELINES[key], f"VOLATILITY_BASELINES[{key}]")

    def compute_volatility(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """
        Compute the volatility identity for a matchup between two teams.

        Returns a dict containing at least:
            - "engine_version"
            - "home_team"
            - "away_team"
            - "volatility_score" (float)
            - "volatility_flag" (str: "LOW" | "MEDIUM" | "HIGH")
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
        neutral_volatility = self._get_baseline("neutral_volatility")
        high_threshold = self._get_baseline("high_volatility_threshold")
        low_threshold = self._get_baseline("low_volatility_threshold")
        home_weight = self._get_baseline("home_volatility_weight")
        away_weight = self._get_baseline("away_volatility_weight")
        chaos_weight = self._get_baseline("chaos_weight")
        pace_weight = self._get_baseline("pace_weight")

        # Core identity metrics
        home_volatility = home_profile["volatility"]
        away_volatility = away_profile["volatility"]
        home_chaos = home_profile["chaos"]
        away_chaos = away_profile["chaos"]
        home_pace = home_profile["pace"]
        away_pace = away_profile["pace"]

        # Weighted volatility contribution from each team
        total_weight = home_weight + away_weight if (home_weight + away_weight) != 0 else 1.0
        raw_volatility = (
            home_volatility * home_weight + away_volatility * away_weight
        ) / total_weight

        # Average chaos and pace
        avg_chaos = (home_chaos + away_chaos) / 2.0
        avg_pace = (home_pace + away_pace) / 2.0

        # Components
        #   - base volatility relative to 5.0 neutral
        #   - chaos component: higher chaos → more volatility
        #   - pace component: faster games tend to increase volatility
        base_component = (raw_volatility - 5.0)
        chaos_component = chaos_weight * (avg_chaos - 5.0)
        pace_component = pace_weight * (avg_pace - 5.0)

        # Final volatility score
        volatility_score = neutral_volatility + base_component + chaos_component + pace_component

        # Determine volatility flag
        if volatility_score >= high_threshold:
            volatility_flag = "HIGH"
        elif volatility_score <= low_threshold:
            volatility_flag = "LOW"
        else:
            volatility_flag = "MEDIUM"

        # Clean numeric output
        volatility_score_out = float(round(volatility_score, 3))
        raw_volatility_out = float(round(raw_volatility, 3))
        avg_chaos_out = float(round(avg_chaos, 3))
        avg_pace_out = float(round(avg_pace, 3))
        base_component_out = float(round(base_component, 3))
        chaos_component_out = float(round(chaos_component, 3))
        pace_component_out = float(round(pace_component, 3))

        result: Dict[str, Any] = {
            "engine_version": self.version,
            "home_team": home_code,
            "away_team": away_code,
            "volatility_score": volatility_score_out,
            "volatility_flag": volatility_flag,
            "notes": "Volatility Engine v3.4 matchup volatility identity.",
            "debug": {
                "home_profile": home_profile,
                "away_profile": away_profile,
                "baselines": {
                    "neutral_volatility": neutral_volatility,
                    "high_volatility_threshold": high_threshold,
                    "low_volatility_threshold": low_threshold,
                    "home_volatility_weight": home_weight,
                    "away_volatility_weight": away_weight,
                    "chaos_weight": chaos_weight,
                    "pace_weight": pace_weight,
                },
                "intermediate": {
                    "home_volatility": home_volatility,
                    "away_volatility": away_volatility,
                    "home_chaos": home_chaos,
                    "away_chaos": away_chaos,
                    "home_pace": home_pace,
                    "away_pace": away_pace,
                    "raw_volatility": raw_volatility_out,
                    "avg_chaos": avg_chaos_out,
                    "avg_pace": avg_pace_out,
                    "base_component": base_component_out,
                    "chaos_component": chaos_component_out,
                    "pace_component": pace_component_out,
                    "volatility_score": volatility_score_out,
                },
            },
        }

        return result


def compute_volatility_matchup(home_team: str, away_team: str) -> Dict[str, Any]:
    """
    Convenience wrapper that instantiates VolatilityEngine and calls compute_volatility.
    """
    engine = VolatilityEngine()
    return engine.compute_volatility(home_team, away_team)


if __name__ == "__main__":
    sample = compute_volatility_matchup("HOR", "DEN")
    print("✅ VolatilityEngine self-test result:")
    print(sample)
