# FILE: pist01beat/integration_engine.py
"""
Integration Engine v3.4 — MINIMAL WIRING LAYER

This module glues together the verified core engines:

- IdentityEngine   → baseline matchup identity (any return type)
- ChaosEngine      → chaos info (any return type)
- VolatilityEngine → volatility info (any return type)

This version is intentionally minimal:
- It does NOT inspect fields.
- It does NOT call .get() or assume dicts.
- It simply calls the engines and packages their raw outputs
  into a single unified state dict.

Goal: be impossible to break due to return-type changes.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .identity_engine import IdentityEngine
from .chaos_engine import ChaosEngine
from .volatility_engine import VolatilityEngine


class IntegrationEngine:
    """
    Minimal Integration Engine v3.4

    Responsibilities:
    - Own instances of IdentityEngine, ChaosEngine, VolatilityEngine.
    - Run them in a consistent order for a given matchup.
    - Return a single unified state dict containing their *raw* outputs.

    This engine does NOT:
    - Interpret fields
    - Make betting decisions
    - Depend on any particular return type from the engines
    """

    ENGINE_VERSION = "3.4-integration-minimal"

    def __init__(
        self,
        identity_engine: Optional[IdentityEngine] = None,
        chaos_engine: Optional[ChaosEngine] = None,
        volatility_engine: Optional[VolatilityEngine] = None,
    ) -> None:
        self.identity_engine = identity_engine or IdentityEngine()
        self.chaos_engine = chaos_engine or ChaosEngine()
        self.volatility_engine = volatility_engine or VolatilityEngine()

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
            Dict containing raw outputs from all three engines.
        """
        home_team = home_team.strip().upper()
        away_team = away_team.strip().upper()

        if not home_team or not away_team:
            raise ValueError("home_team and away_team must be non-empty strings.")

        if home_team == away_team:
            raise ValueError("home_team and away_team must be different teams.")

        # Call core engines — we do NOT care what types they return.
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

        # Unified state: just bundle raw outputs.
        integrated_state: Dict[str, Any] = {
            "engine_version": self.ENGINE_VERSION,
            "home_team": home_team,
            "away_team": away_team,
            "identity": identity_result,
            "chaos": chaos_result,
            "volatility": volatility_result,
            "debug": {
                "identity_type": type(identity_result).__name__,
                "chaos_type": type(chaos_result).__name__,
                "volatility_type": type(volatility_result).__name__,
            },
        }

        return integrated_state


def compute_integrated_state(
    home_team: str,
    away_team: str,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience wrapper so callers can do:

        from pist01beat.integration_engine import compute_integrated_state
        state = compute_integrated_state("HOR", "DEN")
    """
    engine = IntegrationEngine()
    return engine.compute_integrated_state(
        home_team=home_team,
        away_team=away_team,
        notes=notes,
    )


if __name__ == "__main__":
    # Simple smoke test / example usage.
    from pprint import pprint

    demo = compute_integrated_state("HOR", "DEN")
    pprint(demo)
