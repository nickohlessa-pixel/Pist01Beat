# FILE: pist01beat/model.py
"""
Pist01 Beat v3.4 — High-level wrapper.

Single public entrypoint:

    from pist01beat import Pist01Beat

This wrapper delegates the full pipeline to IntegrationEngine,
which is responsible for calling all underlying engines and
returning the final spread/total output.
"""

from typing import Any, Dict

from .integration_engine import IntegrationEngine


class Pist01Beat:
    """
    High-level Pist01 Beat v3.4 wrapper.
    """

    def __init__(self) -> None:
        # Orchestration layer that runs the full pipeline.
        # IntegrationEngine is expected to call the underlying
        # engines (identity, chaos, volatility, etc.) internally.
        self.integration_engine = IntegrationEngine()

    def predict(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """
        Run the full v3.4 pipeline for a matchup.

        Returns a dict with at least:
        - engine_version
        - home_team
        - away_team
        - model_spread
        - model_total
        plus any engine/debug payload.
        """
        result = self.integration_engine.run(home_team, away_team)

        # Hard guard against any leftover bootstrap wiring.
        version = str(result.get("engine_version", ""))
        if "wrapper-bootstrap" in version:
            raise RuntimeError(
                "Bootstrap wrapper output detected; integration is still returning a placeholder."
            )

        debug = result.get("debug")
        if isinstance(debug, dict):
            note = str(debug.get("note", ""))
            if "Bootstrap placeholder" in note:
                raise RuntimeError(
                    "Bootstrap placeholder debug note detected; engines are not wired correctly."
                )

        return result
