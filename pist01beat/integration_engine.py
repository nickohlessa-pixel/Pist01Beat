# FILE: pist01beat/integration_engine.py
"""
Integration Engine v3.4 — Pist01 Beat

This module glues together the verified core engines:

- IdentityEngine   → baseline matchup identity (spread/total, style, etc.)
- ChaosEngine      → chaos_score + chaos_flag + debug
- VolatilityEngine → volatility_score + volatility_flag + debug

It exposes a small, deterministic IntegrationEngine that:
- Takes (home_team, away_team, optional notes)
- Calls each engine with those inputs
- Returns a single, unified state dict

This is a *wiring* layer only.
No NBA data, no betting logic, no external side effects.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .identity_engine import IdentityEngine
from .chaos_engine import ChaosEngine
from .volatility_engine import VolatilityEngine


class IntegrationEngine:
    """
    Integration Engine v3.4

    Responsibilities:
    - Own instances of IdentityEngine, ChaosEngine, VolatilityEngine
    - Run them in a consistent order for a given matchup
    - Merge their outputs into a single structured state

    This engine does NOT:
    - Fetch or mutate any config
    - Make betting decisions
    - Know anything about real-world NBA data
    """

    ENGINE_VERSION = "3.4-integration"

    def __init__(
        self,
        identity_engine: Optional[IdentityEngine] = None,
        chaos_engine: Optional[ChaosEngine] = None,
        volatility_engine: Optional[VolatilityEngine] = None,
    ) -> None:
        # Allow dependency injection for tests, but default to real engines.
        self.identity_engine = identity_engine or IdentityEngine()
        self.chaos_engine = chaos_engine or ChaosEngine()
        self.volatility_engine = volatility_engine or VolatilityEngine()

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def compute_integrated_state(
        self,
        home_team: str,
        away_team: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute the unified model state for a single matchup.

        Parameters
        ----------
        home_team : str
            Home team code (e.g., "HOR").
        away_team : str
            Away team code (e.g., "DEN").
        notes : Optional[str]
            Optional freeform notes/context for ChaosEngine.

        Returns
        -------
        Dict[str, Any]
            A structured dict combining identity, chaos, and volatility.
        """
        home_team = home_team.strip().upper()
        away_team = away_team.strip().upper()

        if not home_team or not away_team:
            raise ValueError("home_team and away_team must be non-empty strings.")

        if home_team == away_team:
            raise ValueError("home_team and away_team must be different teams.")

        # 1) Core engines
        identity_result = self.identity_engine.compute_identity(
            home_team=home_team,
            away_team=away_team,
        )

        chaos_result = self.chaos_engine.compute_chaos(
            home_team=home_team,
            away_team=away_team,
            notes=notes,
        )

        volatility_result = self.volatility_engine.compute_volatility(
            home_team=home_team,
            away_team=away_team,
        )

        # 2) Light summary lens across engines
        summary: Dict[str, Any] = {
            # Identity-derived
            "base_spread": identity_result.get("base_spread"),
            "base_total": identity_result.get("base_total"),
            "pace_factor": identity_result.get("pace_factor"),
            "power_diff": identity_result.get("power_diff"),
            # Chaos + volatility health flags
            "chaos_flag": chaos_result.get("chaos_flag"),
            "chaos_score": chaos_result.get("chaos_score"),
            "volatility_flag": volatility_result.get("volatility_flag"),
            "volatility_score": volatility_result.get("volatility_score"),
        }

        # 3) Full integrated state
        integrated_state: Dict[str, Any] = {
            "engine_version": self.ENGINE_VERSION,
            "home_team": home_team,
            "away_team": away_team,
            "summary": summary,
            "identity": identity_result,
            "chaos": chaos_result,
            "volatility": volatility_result,
            "debug": {
                "input": {
                    "home_team": home_team,
                    "away_team": away_team,
                    "notes": notes,
                },
                "identity_debug": identity_result.get("debug"),
                "chaos_debug": chaos_result.get("debug"),
                "volatility_debug": volatility_result.get("debug"),
            },
        }

        return integrated_state


# ------------------------------------------------------------------------- #
# Convenience function
# ------------------------------------------------------------------------- #
def compute_integrated_state(
    home_team: str,
    away_team: str,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience wrapper so callers can do:

        from pist01beat.integration_engine import compute_integrated_state
        state = compute_integrated_state("HOR", "DEN")

    without manually instantiating IntegrationEngine.
    """
    engine = IntegrationEngine()
    return engine.compute_integrated_state(home_team=home_team, away_team=away_team, notes=notes)


if __name__ == "__main__":
    # Simple smoke test / example usage (safe to ignore in production).
    demo = compute_integrated_state("HOR", "DEN")
    # Print only the high-level summary for quick inspection.
    from pprint import pprint
    pprint(demo["summary"])
