"""
Volatility Engine v3.4

Simple, deterministic structural volatility layer for Pist01 Beat.

This engine:
- DOES NOT use real NBA data
- Produces a repeatable volatility_score in [0, 1]
- Labels environment with LOW / MEDIUM / HIGH
- Mirrors structure of Chaos Engine for symmetry

Interface:
    from pist01beat.volatility_engine import VolatilityEngine

    engine = VolatilityEngine()
    result = engine.compute_volatility("HOR", "DEN")
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any


ENGINE_VERSION = "3.4-volatility"


@dataclass
class VolatilityResult:
    engine: str
    engine_version: str
    home_team: str
    away_team: str
    volatility_score: float
    volatility_flag: str
    debug: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class VolatilityEngine:
    """
    Deterministic volatility layer using team-code hashing.
    Maintains API symmetry with Chaos Engine for downstream integration.
    """

    def __init__(
        self,
        base_floor: float = 0.10,
        base_ceiling: float = 0.70,
        low_threshold: float = 0.25,
        high_threshold: float = 0.50,
    ) -> None:
        """
        Parameters define the volatility range:
        - base_floor / base_ceiling:
              output range for hash-derived volatility
        - low_threshold / high_threshold:
              cutoffs for LOW / MEDIUM / HIGH labels
        """
        self.base_floor = float(base_floor)
        self.base_ceiling = float(base_ceiling)
        self.low_threshold = float(low_threshold)
        self.high_threshold = float(high_threshold)

    # ------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------
    @staticmethod
    def _team_hash(team_code: str) -> int:
        """
        Deterministic hash from team code characters only.
        """
        team_code = (team_code or "").upper().strip()
        if not team_code:
            return 0
        return sum(ord(ch) for ch in team_code)

    def _pair_hash(self, home_code: str, away_code: str) -> int:
        """
        Combine team-code hashes into a single deterministic number.
        """
        h = self._team_hash(home_code)
        a = self._team_hash(away_code)
        return (h * 13 + a * 29) % 1000  # 0..999

    def _normalize(self, raw: int) -> float:
        """
        Map raw 0..999 into [base_floor, base_ceiling].
        """
        span = self.base_ceiling - self.base_floor
        return self.base_floor + span * (raw / 999.0)

    def _label(self, score: float) -> str:
        """
        Assign LOW / MEDIUM / HIGH volatility label.
        """
        if score < self.low_threshold:
            return "LOW"
        if score < self.high_threshold:
            return "MEDIUM"
        return "HIGH"

    # ------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------
    def compute_volatility(self, home_team: str, away_team: str) -> VolatilityResult:
        """
        Compute volatility_score and volatility_flag for a matchup.
        """
        home_code = (home_team or "").upper().strip()
        away_code = (away_team or "").upper().strip()

        raw = self._pair_hash(home_code, away_code)
        volatility_score = self._normalize(raw)

        volatility_flag = self._label(volatility_score)

        debug: Dict[str, Any] = {
            "home_code": home_code,
            "away_code": away_code,
            "raw_hash": raw,
            "params": {
                "base_floor": self.base_floor,
                "base_ceiling": self.base_ceiling,
                "low_threshold": self.low_threshold,
                "high_threshold": self.high_threshold,
            },
        }

        return VolatilityResult(
            engine="volatility",
            engine_version=ENGINE_VERSION,
            home_team=home_code,
            away_team=away_code,
            volatility_score=volatility_score,
            volatility_flag=volatility_flag,
            debug=debug,
        )
