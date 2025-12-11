# FILE: pist01beat/model.py
"""
Pist01 Beat v3.4 — high-level wrapper.

Public entrypoint:

    from pist01beat import Pist01Beat

This wrapper delegates to IntegrationEngine, which returns the
full engine stack output (identity, chaos, volatility, spread).
predict() normalizes that into stable spread/total lines and
never hard-crashes; errors are surfaced in debug.
"""

from dataclasses import asdict, is_dataclass
from typing import Any, Dict
import traceback

from .integration_engine import IntegrationEngine


class Pist01Beat:
    """High-level Pist01 Beat v3.4 wrapper."""

    def __init__(self) -> None:
        # Single orchestration layer that runs the full pipeline
        self.integration = IntegrationEngine()

    # ----------------------------
    # Helpers
    # ----------------------------
    @staticmethod
    def _to_dict(obj: Any) -> Dict[str, Any]:
        """
        Convert dataclasses, dicts, or simple objects into a dict
        for unified access. Safe, no exceptions thrown.
        """
        if obj is None:
            return {}

        if isinstance(obj, dict):
            return obj

        if is_dataclass(obj):
            return asdict(obj)

        out: Dict[str, Any] = {}
        for name in dir(obj):
            if name.startswith("_"):
                continue
            try:
                out[name] = getattr(obj, name)
            except Exception:
                continue
        return out

    # ----------------------------
    # Public API
    # ----------------------------
    def predict(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """
        Run the full v3.4 stack and return:

        {
            "engine_version": str,
            "home_team": str,
            "away_team": str,
            "model_spread": float,
            "model_total": float,
            "debug": { ... full engine results OR error info ... }
        }

        This method is error-safe:
        - On success: returns real model lines.
        - On failure: returns 0/0 lines and an error payload in debug.
        """
        try:
            # 1) Run full pipeline
            result = self.integration.run(home_team=home_team, away_team=away_team)

            # 2) Normalize result object → dict
            res = self._to_dict(result)

            # Extract engine_version (integration, spread, or fallback)
            engine_version = (
                res.get("engine_version")
                or self._to_dict(res.get("spread", {})).get("engine_version")
                or "3.4-wrapper-integration"
            )

            # Extract components for debug
            identity = res.get("identity")
            chaos = res.get("chaos")
            volatility = res.get("volatility")
            spread_obj = res.get("spread")

            spread_dict = self._to_dict(spread_obj)

            # Choose correct spread attributes
            model_spread = (
                spread_dict.get("final_spread")
                if "final_spread" in spread_dict
                else spread_dict.get("base_spread")
            )

            model_total = (
                spread_dict.get("final_total")
                if "final_total" in spread_dict
                else spread_dict.get("base_total")
            )

            # Final safety defaults
            if model_spread is None:
                model_spread = 0.0
            if model_total is None:
                model_total = 0.0

            return {
                "engine_version": engine_version,
                "home_team": home_team,
                "away_team": away_team,
                "model_spread": model_spread,
                "model_total": model_total,
                "debug": {
                    "identity": identity,
                    "chaos": chaos,
                    "volatility": volatility,
                    "spread": spread_obj,
                    "integration_raw": result,
                },
            }

        except Exception as e:
            # Hard fail-safe: never crash Game Day threads.
            return {
                "engine_version": "3.4-wrapper-error",
                "home_team": home_team,
                "away_team": away_team,
                "model_spread": 0.0,
                "model_total": 0.0,
                "debug": {
                    "error": repr(e),
                    "traceback": traceback.format_exc(),
                },
            }
