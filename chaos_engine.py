# FILE: chaos_engine.py
"""
Chaos Engine for Pist01 Beat v3.4.

This module converts team identity profiles into a game-level chaos score
and chaos flag using only configuration data and simple, deterministic math.

It is intentionally lightweight:
- pulls team profiles and chaos baselines from config.py
- uses pace, chaos, and volatility traits to derive a chaos_score
- returns a structured dict for consumption by other engines
"""

from typing import Any, Dict
import math

import load_config  # noqa: F401 (imported for side-effects / future use)

from config import TEAM_PROFILES, MODEL_VERSION, CHAOS_BASELINES

# Try to import engine-specific errors; provide local fallbacks if unavailable.
try:
    from errors import TeamProfileError, CalculationError  # type: ignore
except Exception:  # pragma: no cover

    class TeamProfileError(Exception):
        """Raised when a team profile is missing or malformed."""

    class CalculationError(Exception):
        """Raised when chaos calculations cannot be completed."""


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


class ChaosEngine:
    """
    Chaos Engine v3.4

    Responsible for:
    - Turning team chaos/volatility/pace identity into a matchup-level chaos signal
    - Producing a chaos_score and chaos_flag BEFORE other adjustments
    """

    def __init__(self, model_version: str | None = None) -> None:
        """
        Initialize the Chaos Engine.

        Args:
            model_version: Optional explicit version string. If None, defaults
                           to MODEL_VERSION from config.py.
        """
        self.version: str = model_version or str(MODEL_VERSION)

    def _get_baseline(self, key: str) -> float:
        """
        Fetch and coerce a baseline value from CHAOS_BASELINES.

        Raises:
            CalculationError: if the key is missing or not convertible.
        """
        if not isinstance(CHAOS_BASELINES, dict):
            raise CalculationError("CHAOS_BASELINES must be a dict in config.py")

        if key not in CHAOS_BASELINES:
            raise CalculationError(
                f"Missing baseline key '{key}' in CHAOS_BASELINES."
            )

        return _coerce_float(CHAOS_BASELINES[key], f"CHAOS_BASELINES[{key}]")

    def compute_chaos(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """
        Compute the chaos identity for a matchup between two teams.

        Returns a dict containing at least:
            - "engine_version"
            - "home_team"
            - "away_team"
            - "chaos_score" (float)
            - "chaos_flag" (str: "LOW" | "MEDIUM" | "HIGH")
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
        neutral_chaos = self._get_baseline("neutral_chaos")
        high_threshold = self._get_baseline("high_chaos_threshold")
        low_threshold = self._get_baseline("low_chaos_threshold")
        home_weight = self._get_baseline("home_chaos_weight")
        away_weight = self._get_baseline("away_chaos_weight")
        volatility_weight = self._get_baseline("volatility_weight")
        pace_weight = self._get_baseline("pace_weight")

        # Core identity metrics
        home_chaos = home_profile["chaos"]
        away_chaos = away_profile["chaos"]
        home_volatility = home_profile["volatility"]
        away_volatility = away_profile["volatility"]
        home_pace = home_profile["pace"]
        away_pace = away_profile["pace"]

        # Weighted chaos contribution from each team
        total_weight = home_weight + away_weight if (home_weight + away_weight) != 0 else 1.0
        raw_chaos = (home_chaos * home_weight + away_chaos * away_weight) / total_weight

        # Volatility and pace factors
        avg_volatility = (home_volatility + away_volatility) / 2.0
        avg_pace = (home_pace + away_pace) / 2.0

        volatility_component = volatility_weight * (avg_volatility - 5.0)
        pace_component = pace_weight * (avg_pace - 5.0)

        # Final chaos score:
        #   neutral_chaos is the baseline
        #   raw_chaos captures team identity
        #   volatility/pace adjust up or down
        chaos_score = neutral_chaos + (raw_chaos - 5.0) + volatility_component + pace_component

        # Determine chaos flag
        if chaos_score >= high_threshold:
            chaos_flag = "HIGH"
        elif chaos_score <= low_threshold:
            chaos_flag = "LOW"
        else:
            chaos_flag = "MEDIUM"

        # Clean numeric output
        chaos_score_out = float(round(chaos_score, 3))
        raw_chaos_out = float(round(raw_chaos, 3))
        avg_volatility_out = float(round(avg_volatility, 3))
        avg_pace_out = float(round(avg_pace, 3))
        volatility_component_out = float(round(volatility_component, 3))
        pace_component_out = float(round(pace_component, 3))

        result: Dict[str, Any] = {
            "engine_version": self.version,
            "home_team": home_code,
            "away_team": away_code,
            "chaos_score": chaos_score_out,
            "chaos_flag": chaos_flag,
            "notes": "Chaos Engine v3.4 matchup chaos identity.",
            "debug": {
                "home_profile": home_profile,
                "away_profile": away_profile,
                "baselines": {
                    "neutral_chaos": neutral_chaos,
                    "high_chaos_threshold": high_threshold,
                    "low_chaos_threshold": low_threshold,
                    "home_chaos_weight": home_weight,
                    "away_chaos_weight": away_weight,
                    "volatility_weight": volatility_weight,
                    "pace_weight": pace_weight,
                },
                "intermediate": {
                    "home_chaos": home_chaos,
                    "away_chaos": away_chaos,
                    "home_volatility": home_volatility,
                    "away_volatility": away_volatility,
                    "home_pace": home_pace,
                    "away_pace": away_pace,
                    "raw_chaos": raw_chaos_out,
                    "avg_volatility": avg_volatility_out,
                    "avg_pace": avg_pace_out,
                    "volatility_component": volatility_component_out,
                    "pace_component": pace_component_out,
                    "chaos_score": chaos_score_out,
                },
            },
        }

        return result


def compute_chaos_matchup(home_team: str, away_team: str) -> Dict[str, Any]:
    """
    Convenience wrapper that instantiates ChaosEngine and calls compute_chaos.
    """
    engine = ChaosEngine()
    return engine.compute_chaos(home_team, away_team)


if __name__ == "__main__":
    sample = compute_chaos_matchup("HOR", "DEN")
    print("✅ ChaosEngine self-test result:")
    print(sample)
