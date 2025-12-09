# FILE: pist01beat/model.py
"""
Pist01 Beat v3.4 — High-level wrapper.

This is the single entrypoint:
    from pist01beat import Pist01Beat

It delegates the full pipeline to IntegrationEngine, which is
responsible for calling the underlying engines and returning
the final spread/total output.
"""

from typing import Any, Dict

from .identity_engine import IdentityEngine
from .chaos_engine import ChaosEngine
from .volatility_engine import VolatilityEngine
from .integration_engine import IntegrationEngine


class Pist01Beat:
    """
    High-level v3.4 model wrapper.
    """

    def __init__(self) -> None:
        # Expose engines in case you ever want them directly
        self.identity_engine = IdentityEngine()
        self.chaos_engine = ChaosEngine()
        self.volatility_engine = VolatilityEngine()

        # Orchestration layer that runs the full pipeline
        # (must already know how to call the engines above)
        self.integration_engine = IntegrationEngine()

    def predict(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """
        Run the full v3.4 pipeline for a matchup.

        Must return a dict with at least:
        - engine_version
        - home_team
        - away_team
        - model_spread
        - model_total
        plus any debug payload from the engines.
        """
        result = self.integration_engine.run(home_team, away_team)

        # Sanity guard against old bootstrap artifacts
        if result.get("engine_version") == "3.4-wrapper-bootstrap":
            raise RuntimeError("Bootstrap wrapper is still being returned somewhere in the stack.")

        if "debug" in result and isinstance(result["debug"], dict):
            note = result["debug"].get("note", "")
            if isinstance(note, str) and "Bootstrap placeholder" in note:
                raise RuntimeError("Bootstrap debug note detected; integration is not using real engines.")

        return result
