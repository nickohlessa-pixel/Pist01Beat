"""
Identity Engine v3.4

Lightweight, deterministic identity layer for Pist01 Beat.

This engine:
- DOES NOT use any external NBA data
- DOES provide a stable, repeatable interface for downstream engines
- Returns:
    - pace_factor
    - power_diff
    - base_spread
    - base_total
    - full debug block

Notes:
- This is a structural / plumbing implementation for Project 15.
- Actual basketball truth will be layered in via config + later projects.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any


ENGINE_VERSION = "3.4-identity"


@dataclass
class IdentityResult:
    engine: str
    engine_version: str
    home_team: str
    away_team: str
    pace_factor: float
    power_diff: float
    base_spread: float
    base_total: float
    debug: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IdentityEngine:
    """
    Deterministic identity layer.

    Interface:
        engine = IdentityEngine()
        result = engine.compute_identity("HOR", "DEN")
        # result is an IdentityResult, or use result.to_dict()
    """

    def __init__(
        self,
        base_total_anchor: float = 225.0,
        max_pace_adjust: float = 15.0,
        power_scale: float = 25.0,
    ) -> None:
        """
        Parameters are intentionally simple; they are structural, not 'true' NBA knobs.
        - base_total_anchor: baseline total before pace adjustments
        - max_pace_adjust: how many points total can move based on pace_factor
        - power_scale: divisor used to scale pseudo power_diff from team hashes
        """
        self.base_total_anchor = float(base_total_anchor)
        self.max_pace_adjust = float(max_pace_adjust)
        self.power_scale = float(power_scale)

    # ------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------
    @staticmethod
    def _team_hash(team_code: str) -> int:
        """
        Simple deterministic hash based only on team code characters.
        Keeps us fully self-contained and non-random.
        """
        team_code = (team_code or "").upper().strip()
        if not team_code:
            return 0
        return sum(ord(ch) for ch in team_code)

    def _compute_pace_factor(self, home_hash: int, away_hash: int) -> float:
        """
        Derive a pseudo pace factor from the pair of team hashes.
        Output is roughly in [0.85, 1.15] but deterministic.
        """
        raw = (home_hash + away_hash) % 31  # 0..30
        normalized = raw / 30.0  # 0..1
        # Map into [0.85, 1.15]
        return 0.85 + 0.30 * normalized

    def _compute_power_diff(self, home_hash: int, away_hash: int) -> float:
        """
        Derive a pseudo power_diff signal from the team hashes.

        Positive power_diff  -> home team stronger
        Negative power_diff  -> away team stronger
        """
        diff = home_hash - away_hash
        return diff / self.power_scale

    # ------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------
    def compute_identity(self, home_team: str, away_team: str) -> IdentityResult:
        """
        Core entry point for the Identity Engine.

        Returns an IdentityResult with:
        - pace_factor
        - power_diff
        - base_spread  (home - away)
        - base_total
        - debug dict
        """
        home_team_code = (home_team or "").upper().strip()
        away_team_code = (away_team or "").upper().strip()

        home_hash = self._team_hash(home_team_code)
        away_hash = self._team_hash(away_team_code)

        pace_factor = self._compute_pace_factor(home_hash, away_hash)
        power_diff = self._compute_power_diff(home_hash, away_hash)

        # Home - away spread; negative means our model leans to the away side.
        base_spread = round(-power_diff, 1)

        # Total anchored on base_total_anchor with pace adjustment
        pace_offset = (pace_factor - 1.0) * self.max_pace_adjust
        base_total = round(self.base_total_anchor + pace_offset, 1)

        debug: Dict[str, Any] = {
            "home_team_code": home_team_code,
            "away_team_code": away_team_code,
            "home_hash": home_hash,
            "away_hash": away_hash,
            "pace_offset": pace_offset,
            "params": {
                "base_total_anchor": self.base_total_anchor,
                "max_pace_adjust": self.max_pace_adjust,
                "power_scale": self.power_scale,
            },
        }

        return IdentityResult(
            engine="identity",
            engine_version=ENGINE_VERSION,
            home_team=home_team_code,
            away_team=away_team_code,
            pace_factor=pace_factor,
            power_diff=power_diff,
            base_spread=base_spread,
            base_total=base_total,
            debug=debug,
        )
