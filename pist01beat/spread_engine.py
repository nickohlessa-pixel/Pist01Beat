"""
SpreadEngine v3.4 — minimal stub.

This is a temporary implementation so IntegrationEngine can:
- Import SpreadEngine
- Call compute_lines(...)
- Receive a structured spread/total result.

Logic:
- Uses identity.base_spread and identity.base_total as the model outputs.
- Attaches chaos and volatility info only in debug for now.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict


ENGINE_VERSION = "3.4-spread-minimal"


@dataclass
class SpreadLines:
    engine: str
    engine_version: str
    home_team: str
    away_team: str
    model_spread: float
    model_total: float
    debug: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SpreadEngine:
    """
    Minimal SpreadEngine interface.

    Expected usage (from IntegrationEngine):

        engine = SpreadEngine()
        result = engine.compute_lines(
            home_team="HOR",
            away_team="DEN",
            identity=identity_result,
            chaos=chaos_result,
            volatility=volatility_result,
        )

    For now, this just passes through identity.base_spread and identity.base_total.
    """

    def compute_lines(
        self,
        home_team: str,
        away_team: str,
        identity: Any,
        chaos: Any,
        volatility: Any,
    ) -> SpreadLines:
        # Identity is expected to be either an IdentityResult dataclass
        # or a dict-like object with base_spread/base_total attributes/keys.
        base_spread = getattr(identity, "base_spread", None)
        base_total = getattr(identity, "base_total", None)

        # Fallback if identity is a dict instead of a dataclass
        if base_spread is None and isinstance(identity, dict):
            base_spread = identity.get("base_spread")
        if base_total is None and isinstance(identity, dict):
            base_total = identity.get("base_total")

        if base_spread is None or base_total is None:
            raise ValueError(
                "SpreadEngine.compute_lines expected identity to provide "
                "base_spread and base_total."
            )

        debug: Dict[str, Any] = {
            "identity_type": type(identity).__name__,
            "chaos_type": type(chaos).__name__,
            "volatility_type": type(volatility).__name__,
        }

        return SpreadLines(
            engine="spread",
            engine_version=ENGINE_VERSION,
            home_team=home_team,
            away_team=away_team,
            model_spread=base_spread,
            model_total=base_total,
            debug=debug,
        )
