    # Default tuning parameters — must match constants.py if present
    self.CHAOS_WEIGHT = 0.55
    self.PACE_WEIGHT = 0.25
    self.POWER_STABILITY_WEIGHT = 0.20

    # Volatility thresholds for flags
    self.TIER_THRESHOLDS = {
        1: 0.00,
        2: 0.20,
        3: 0.45,
        4: 0.70,
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
    """Convert volatility score into a 1–5 tier."""
    for tier, threshold in reversed(self.TIER_THRESHOLDS.items()):
        if score >= threshold:
            return tier
    return 1

# ---------------------------------------------------------
# MAIN COMPUTE FUNCTION
# ---------------------------------------------------------

def compute_volatility(
    self,
    home_team: str,
    away_team: str,
    chaos_dict: Dict[str, Any],
    identity_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Computes volatility score for the matchup.
    Inputs:
        - identity_dict: output of Identity Engine
        - chaos_dict: output of Chaos Engine
    """

    if identity_dict is None or chaos_dict is None:
        raise ModelError("VolatilityEngine requires identity_dict and chaos_dict.")

    # Extract identity components
    pace_factor = identity_dict.get("pace_factor", 1.0)
    power_diff = identity_dict.get("power_diff", 0.0)
    base_identity_vol = identity_dict.get("identity_volatility", 0.10)

    # Extract chaos components
    chaos_score = chaos_dict.get("chaos_score", 0.0)

    # ------------------------------
    # Volatility Component Assembly
    # ------------------------------

    chaos_component = chaos_score * self.CHAOS_WEIGHT
    pace_component = abs(pace_factor - 1.0) * self.PACE_WEIGHT
    power_stability = (
        1.0 - clamp(abs(power_diff) / 10.0, 0.0, 1.0)
    ) * self.POWER_STABILITY_WEIGHT

    raw_volatility = (
        chaos_component
        + pace_component
        + base_identity_vol
        - power_stability
    )

    volatility_score = clamp(raw_volatility, 0.0, 1.0)

    # ------------------------------
    # Tier + Flag Mapping
    # ------------------------------

    volatility_tier = self._map_score_to_tier(volatility_score)
    volatility_flag = self.FLAG_MAP[volatility_tier]

    # ------------------------------
    # OUTPUT
    # ------------------------------

    return {
        "home_team": home_team,
        "away_team": away_team,
        "volatility_score": float(volatility_score),
        "volatility_flag": volatility_flag,
        "volatility_tier": volatility_tier,
        "debug": {
            "pace_factor": pace_factor,
            "power_diff": power_diff,
            "base_identity_volatility": base_identity_vol,
            "chaos_score": chaos_score,
            "chaos_component": chaos_component,
            "pace_component": pace_component,
            "power_stability_component": power_stability,
            "raw_volatility": raw_volatility,
        },
    }
