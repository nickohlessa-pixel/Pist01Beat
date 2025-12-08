%%writefile chaos_engine.py
# FILE: chaos_engine.py
"""
Chaos Engine v3.4
Computes game-level chaos score using identity and structural factors.
This engine is deterministic and matches Model Brain v3.4 architecture.
"""

from typing import Dict, Any
from utils import clamp, safe_divide
from errors import ModelError


class ChaosEngine:
    def __init__(self, config=None):
        self.config = config

        # Tuning parameters (should align with constants.py if/when centralized)
        self.PACE_WEIGHT = 0.5          # How much extreme pace adds to chaos
        self.IDENTITY_VOL_WEIGHT = 0.4  # How much identity volatility adds to chaos
        self.POWER_PARITY_WEIGHT = 0.3  # How much close power matchups add to chaos

        # Chaos tiers
        self.TIER_THRESHOLDS = {
            1: 0.00,
            2: 0.25,
            3: 0.50,
            4: 0.75,
            5: 0.90,
        }

        self.FLAG_MAP = {
            1: "LOW",
            2: "LOW",
            3: "MEDIUM",
            4: "HIGH",
            5: "HIGH",
        }

    # ---------------------------------------------------------
    # INTERNAL HELPERS
    # ---------------------------------------------------------

    def _map_score_to_tier(self, score: float) -> int:
        """Convert chaos score into a 1–5 tier."""
        for tier, threshold in reversed(self.TIER_THRESHOLDS.items()):
            if score >= threshold:
                return tier
        return 1

    # ---------------------------------------------------------
    # MAIN COMPUTE FUNCTION
    # ---------------------------------------------------------

    def compute_chaos(
        self,
        home_team: str,
        away_team: str,
        identity_dict: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Compute chaos score for a matchup.

        Parameters
        ----------
        home_team : str
            Home team code (e.g., "HOR").
        away_team : str
            Away team code (e.g., "DEN").
        identity_dict : dict | None
            Output of IdentityEngine for this matchup. If None, uses neutral defaults.
        """

        # Neutral defaults if identity engine output is missing
        if identity_dict is None:
            pace_factor = 1.0
            identity_volatility = 0.15
            power_diff = 0.0
        else:
            pace_factor = identity_dict.get("pace_factor", 1.0)
            identity_volatility = identity_dict.get("identity_volatility", 0.15)
            power_diff = identity_dict.get("power_diff", 0.0)

        # ---------------------------------
        # Chaos component construction
        # ---------------------------------

        # 1) Pace chaos: faster or ultra-slow games are more chaotic
        pace_deviation = abs(pace_factor - 1.0)  # 0 = neutral, >0 = more extreme
        pace_component = pace_deviation * self.PACE_WEIGHT

        # 2) Identity volatility: unstable teams carry chaos with them
        identity_component = identity_volatility * self.IDENTITY_VOL_WEIGHT

        # 3) Power parity: closer games are more chaos-prone
        #    Large power_diff → more predictable → less chaos.
        power_diff_norm = clamp(abs(power_diff) / 10.0, 0.0, 1.0)
        power_parity = 1.0 - power_diff_norm  # 1 when even, 0 when big mismatch
        power_parity_component = power_parity * self.POWER_PARITY_WEIGHT

        raw_chaos = pace_component + identity_component + power_parity_component

        chaos_score = clamp(raw_chaos, 0.0, 1.0)

        # Map to tier + flag
        chaos_tier = self._map_score_to_tier(chaos_score)
        chaos_flag = self.FLAG_MAP[chaos_tier]

        return {
            "home_team": home_team,
            "away_team": away_team,
            "chaos_score": float(chaos_score),
            "chaos_flag": chaos_flag,
            "chaos_tier": chaos_tier,
            "debug": {
                "pace_factor": pace_factor,
                "identity_volatility": identity_volatility,
                "power_diff": power_diff,
                "pace_deviation": pace_deviation,
                "pace_component": pace_component,
                "identity_component": identity_component,
                "power_parity": power_parity,
                "power_parity_component": power_parity_component,
                "raw_chaos": raw_chaos,
            },
        }
