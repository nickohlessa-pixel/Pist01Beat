# FILE: constants.py
"""
Universal static constants for Pist01 Beat v3.4.

These values are intentionally NON-DYNAMIC and do not change based
on matchup, roster state, travel, volatility, or chaos scoring.
They are purely global knobs used by the entire ecosystem.
"""

MODEL_NAME = "Pist01 Beat"
MODEL_VERSION = "3.4"

# Numerical tolerances
EPSILON = 1e-9
SAFE_DIV_ZERO = 1e-6

# Spread/Total calculation limits
MAX_SPREAD_SHIFT = 18.0     # maximum allowed adjustment after all engines
MAX_TOTAL_SHIFT = 28.0      # maximum allowed total adjustment

# Generic weighting constants used across modules
PACE_WEIGHT = 1.0
POWER_WEIGHT = 1.0
CHAOS_WEIGHT = 1.0
VOLATILITY_WEIGHT = 1.0

# Return minimum and maximum allowed predictions
MIN_PREDICTED_TOTAL = 170.0
MAX_PREDICTED_TOTAL = 260.0
MIN_PREDICTED_SPREAD = -25.0
MAX_PREDICTED_SPREAD = 25.0


if __name__ == "__main__":
    print("constants.py loaded successfully.")
