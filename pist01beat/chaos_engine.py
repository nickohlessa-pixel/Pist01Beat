"""
Chaos Engine v3.4

Deterministic 'environment volatility' layer for Pist01 Beat.

This engine:
- DOES NOT use any external NBA data
- Produces a repeatable chaos_score in [0, 1]
- Labels the environment with LOW / MEDIUM / HIGH chaos_flag
- Exposes a structured result for downstream engines

Interface:
    from pist01beat.chaos_engine import ChaosEngine

    engine = ChaosEngine()
    result = engine.compute_chaos("HOR", "DEN")
    # result.chaos_score, result.chaos_flag, result.debug
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional


ENGINE_VERSION = "3.4-chaos"


@dataclass
class ChaosResult:
    engine: str
    engine_version: str
    home_team: str
    away_team: str
    chaos_score: float
    chaos_flag: str
    drivers: List[str]
    debug: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ChaosEngine:
    """
    Deterministic, rule-based Chaos Engine.

    It does NOT know real injuries, referees, or schedule.
    Instead, it uses:
      - team code hashes (structural, repeatable)
      - optional note-tags supplied by upstream layers

    The goal for Project 15:
      - provide a stable chaos_score + chaos_flag
      - keep logic simple and transparent
    """

    def __init__(
        self,
        base_floor: float = 0.15,
        base_ceiling: float = 0.85,
        low_threshold: float = 0.35,
        high_threshold: float = 0.65,
        note_boost_per_tag: float = 0.06,
        max_note_boost: float = 0.18,
    ) -> None:
        """
        Parameters:
        - base_floor / base_ceiling:
            numeric window for hash-derived chaos before note boosts
        - low_threshold / high_threshold:
            boundaries for LOW / MEDIUM / HIGH labels
        - note_boost_per_tag:
            how much each chaos-driving note can bump the score
        - max_note_boost:
            cap on total boost from notes
        """
        self.base_floor = float(base_floor)
        self.base_ceiling = float(base_ceiling)
        self.low_threshold = float(low_threshold)
        self.high_threshold = float(high_threshold)
        self.note_boost_per_tag = float(note_boost_per_tag)
        self.max_note_boost = float(max_note_boost)

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
        Combined, order-sensitive hash for matchup pair.
        """
        h = self._team_hash(home_code)
        a = self._team_hash(away_code)
        # simple mixed hash
        return (h * 31 + a * 17) % 1000  # 0..999

    def _normalize_base_score(self, raw: int) -> float:
        """
        Map raw 0..999 into [base_floor, base_ceiling].
        """
        span = self.base_ceiling - self.base_floor
        return self.base_floor + span * (raw / 999.0)

    def _parse_notes(self, notes: Optional[str]) -> List[str]:
        """
        Notes can be a comma-separated string of chaos drivers,
        e.g. 'injury_uncertainty, rotation_noise'.
        We treat unknown tags as generic chaos drivers.
        """
        if not notes:
            return []

        if isinstance(notes, str):
            raw_tags = [t.strip().lower() for t in notes.split(",")]
        else:
            # Very defensive: if someone passes a list, flatten it.
            try:
                raw_tags = [str(t).strip().lower() for t in notes]  # type: ignore
            except Exception:
                raw_tags = [str(notes).strip().lower()]

        return [t for t in raw_tags if t]

    def _note_boost(self, tags: List[str]) -> float:
        """
        Each tag contributes a fixed boost up to max_note_boost.
        """
        if not tags:
            return 0.0
        boost = len(tags) * self.note_boost_per_tag
        if boost > self.max_note_boost:
            boost = self.max_note_boost
        return boost

    def _label_flag(self, score: float) -> str:
        """
        Convert numeric chaos_score into a flag.
        """
        if score < self.low_threshold:
            return "LOW"
        if score < self.high_threshold:
            return "MEDIUM"
        return "HIGH"

    # ------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------
    def compute_chaos(
        self,
        home_team: str,
        away_team: str,
        notes: Optional[str] = None,
    ) -> ChaosResult:
        """
        Compute chaos_score and chaos_flag for a given matchup.

        Parameters:
        - home_team: home team code (e.g. 'HOR')
        - away_team: away team code (e.g. 'DEN')
        - notes: optional comma-separated chaos tags
                 (e.g. 'injury_uncertainty, rotation_noise')

        Returns:
        - ChaosResult
        """
        home_code = (home_team or "").upper().strip()
        away_code = (away_team or "").upper().strip()

        raw_hash = self._pair_hash(home_code, away_code)
        base_score = self._normalize_base_score(raw_hash)

        tags = self._parse_notes(notes)
        boost = self._note_boost(tags)

        chaos_score = base_score + boost
        # clamp to [0, 1]
        if chaos_score < 0.0:
            chaos_score = 0.0
        elif chaos_score > 1.0:
            chaos_score = 1.0

        chaos_flag = self._label_flag(chaos_score)

        drivers: List[str] = []
        if tags:
            drivers.append("note_tags_present")
        if chaos_flag == "HIGH":
            drivers.append("high_environmental_volatility")
        elif chaos_flag == "MEDIUM":
            drivers.append("moderate_environmental_volatility")
        else:
            drivers.append("stable_environment")

        debug: Dict[str, Any] = {
            "home_code": home_code,
            "away_code": away_code,
            "raw_hash": raw_hash,
            "base_score": base_score,
            "note_tags": tags,
            "note_boost": boost,
            "params": {
                "base_floor": self.base_floor,
                "base_ceiling": self.base_ceiling,
                "low_threshold": self.low_threshold,
                "high_threshold": self.high_threshold,
                "note_boost_per_tag": self.note_boost_per_tag,
                "max_note_boost": self.max_note_boost,
            },
        }

        return ChaosResult(
            engine="chaos",
            engine_version=ENGINE_VERSION,
            home_team=home_code,
            away_team=away_code,
            chaos_score=chaos_score,
            chaos_flag=chaos_flag,
            drivers=drivers,
            debug=debug,
        )
