"""
IntegrationEngine v3.4 — minimal unified state builder.

This engine:
- Normalizes and validates team codes
- Calls IdentityEngine, ChaosEngine, and VolatilityEngine
- Bundles their raw outputs into a single integrated_state dict

Pist01Beat.predict() calls IntegrationEngine.run(), which is a thin wrapper
around compute_state(). Spread/total layering can be added later.
"""

from typing import Dict, Any, Optional

from .identity_engine import IdentityEngine
from .chaos_engine import ChaosEngine
from .volatility_engine import VolatilityEngine


class IntegrationEngine:
    """Orchestrates the core engines into a unified matchup state."""

    ENGINE_VERSION: str = "3.4-integration-minimal"

    def __init__(self) -> None:
        self.identity_engine = IdentityEngine()
        self.chaos_engine = ChaosEngine()
        self.volatility_engine = VolatilityEngine()

    def compute_state(
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
        Public entrypoint used by Pist01Beat.predict().

        For now this just returns the unified engine state. Later we can
        layer derived fields (model_spread, model_total, etc.) on top.
        """
        return self.compute_state(home_team=home_team, away_team=away_team, notes=notes)
