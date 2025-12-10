"""
IntegrationEngine v3.4 — unified state builder with SpreadEngine wiring.

This engine:
- Normalizes and validates team codes
- Calls IdentityEngine, ChaosEngine, VolatilityEngine
- Calls SpreadEngine (v1)
- Bundles outputs into a single integrated_state dict

Pist01Beat.predict() uses IntegrationEngine.run()
"""

from typing import Dict, Any, Optional

from .identity_engine import IdentityEngine
from .chaos_engine import ChaosEngine
from .volatility_engine import VolatilityEngine
from .spread_engine import SpreadEngine


class IntegrationEngine:
    """Orchestrates the core engines into a unified matchup state."""

    ENGINE_VERSION: str = "3.4-integration-v1-spread"

    def __init__(self) -> None:
        self.identity_engine = IdentityEngine()
        self.chaos_engine = ChaosEngine()
        self.volatility_engine = VolatilityEngine()
        self.spread_engine = SpreadEngine()  # NEW

    def compute_state(
        self,
        home_team: str,
        away_team: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute the unified model state for a single matchup.
        """
        home_team = home_team.strip().upper()
        away_team = away_team.strip().upper()

        if not home_team or not away_team:
            raise ValueError("home_team and away_team must be non-empty strings.")

        if home_team == away_team:
            raise ValueError("home_team and away_team must be different teams.")

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

    def run(
        self,
        home_team: str,
        away_team: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        v1-spread:
        - Compute unified state (identity, chaos, volatility)
        - Call SpreadEngine to attach model_spread + model_total
        """
        state = self.compute_state(
            home_team=home_team,
            away_team=away_team,
            notes=notes,
        )

        identity = state["identity"]
        chaos = state["chaos"]
        volatility = state["volatility"]

        spread_result = self.spread_engine.compute_lines(
            home_team=state["home_team"],
            away_team=state["away_team"],
            identity=identity,
            chaos=chaos,
            volatility=volatility,
        )

        state["spread"] = spread_result
        return state
