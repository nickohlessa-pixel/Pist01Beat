# FILE: load_config.py
"""
Centralized loader and validator for Pist01 Beat v3.4 configuration.

This module is the single gateway for accessing:
- config.py (team profiles, baselines, thresholds)
- constants.py (global constants, model metadata)

It:
- imports config + constants
- validates required keys and structures
- exposes safe accessors for other engines

All engines should use this module instead of importing config.py directly.
"""

from typing import Any, Dict, Optional

import importlib

# Local imports (all should live in the same directory)
import config
import constants
from errors import ConfigError


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _require_key(mapping: Dict[str, Any], key: str, context: str) -> Any:
    """
    Ensure a given key exists in a mapping, otherwise raise ConfigError.
    """
    if key not in mapping:
        raise ConfigError(f"Missing key '{key}' in {context}.")
    return mapping[key]


def _validate_number(value: Any, context: str) -> None:
    """
    Ensure value is an int/float and not None.
    """
    if not isinstance(value, (int, float)):
        raise ConfigError(f"Expected numeric value for {context}, got {type(value).__name__}.")


# ============================================================
# PUBLIC METADATA ACCESS
# ============================================================

def get_model_version() -> str:
    """
    Returns the model version from config.py.

    Note: constants.MODEL_VERSION and config.MODEL_VERSION may both exist;
    this function explicitly returns config.MODEL_VERSION.
    """
    if not hasattr(config, "MODEL_VERSION"):
        raise ConfigError("config.MODEL_VERSION is missing.")
    version = config.MODEL_VERSION
    if not isinstance(version, str):
        raise ConfigError("config.MODEL_VERSION must be a string.")
    return version


def get_constants_version() -> Optional[str]:
    """
    Returns the model version from constants.py if present; otherwise None.
    """
    return getattr(constants, "MODEL_VERSION", None)


# ============================================================
# TEAM PROFILES ACCESS
# ============================================================

def get_team_profiles() -> Dict[str, Dict[str, Any]]:
    """
    Return the full TEAM_PROFILES dictionary from config.py after basic validation.
    """
    if not hasattr(config, "TEAM_PROFILES"):
        raise ConfigError("config.TEAM_PROFILES is missing.")

    team_profiles = config.TEAM_PROFILES
    if not isinstance(team_profiles, dict):
        raise ConfigError("config.TEAM_PROFILES must be a dict of team_code -> profile dict.")

    # Minimal structure check for each team
    required_keys = [
        "name",
        "base_power",
        "offense",
        "defense",
        "pace",
        "chaos",
        "volatility",
    ]

    for code, profile in team_profiles.items():
        if not isinstance(profile, dict):
            raise ConfigError(f"Profile for team '{code}' must be a dict.")

        for key in required_keys:
            value = _require_key(profile, key, f"TEAM_PROFILES['{code}']")
            if key == "name":
                if not isinstance(value, str):
                    raise ConfigError(f"'name' for team '{code}' must be a string.")
            else:
                _validate_number(value, f"TEAM_PROFILES['{code}']['{key}']")

    return team_profiles


def get_team_profile(team_code: str) -> Dict[str, Any]:
    """
    Return the profile dict for a given team code.

    Falls back to 'GENERIC' if the code is unknown and GENERIC exists.
    """
    profiles = get_team_profiles()

    if team_code in profiles:
        return profiles[team_code]

    # Optional: fallback to GENERIC
    if "GENERIC" in profiles:
        return profiles["GENERIC"]

    raise ConfigError(f"Unknown team code '{team_code}' and no GENERIC profile defined.")


# ============================================================
# SPREAD / TOTAL BASELINES ACCESS
# ============================================================

def get_spread_total_baselines() -> Dict[str, float]:
    """
    Return SPREAD_TOTAL_BASELINES dict from config.py after validation.
    """
    if not hasattr(config, "SPREAD_TOTAL_BASELINES"):
        raise ConfigError("config.SPREAD_TOTAL_BASELINES is missing.")

    baselines = config.SPREAD_TOTAL_BASELINES
    if not isinstance(baselines, dict):
        raise ConfigError("config.SPREAD_TOTAL_BASELINES must be a dict.")

    required_keys = [
        "default_total",
        "home_edge",
        "pace_spread_scale",
        "pace_total_scale",
        "power_spread_scale",
    ]

    for key in required_keys:
        value = _require_key(baselines, key, "SPREAD_TOTAL_BASELINES")
        _validate_number(value, f"SPREAD_TOTAL_BASELINES['{key}']")

    return baselines


# ============================================================
# CHAOS / VOLATILITY THRESHOLDS ACCESS
# ============================================================

def get_chaos_volatility_thresholds() -> Dict[str, float]:
    """
    Return CHAOS_VOLATILITY_THRESHOLDS dict from config.py after validation.
    """
    if not hasattr(config, "CHAOS_VOLATILITY_THRESHOLDS"):
        raise ConfigError("config.CHAOS_VOLATILITY_THRESHOLDS is missing.")

    thresholds = config.CHAOS_VOLATILITY_THRESHOLDS
    if not isinstance(thresholds, dict):
        raise ConfigError("config.CHAOS_VOLATILITY_THRESHOLDS must be a dict.")

    required_keys = [
        "chaos_low",
        "chaos_high",
        "vol_low",
        "vol_high",
    ]

    for key in required_keys:
        value = _require_key(thresholds, key, "CHAOS_VOLATILITY_THRESHOLDS")
        _validate_number(value, f"CHAOS_VOLATILITY_THRESHOLDS['{key}']")

    return thresholds


# ============================================================
# HOT-RELOAD SUPPORT (OPTIONAL)
# ============================================================

def reload_config_module() -> None:
    """
    Reload the config module at runtime.

    Useful in interactive / notebook environments if config.py is edited
    and we want changes to propagate without restarting the process.
    """
    importlib.reload(config)


# ============================================================
# SELF-TEST
# ============================================================

def validate_all() -> None:
    """
    Run a simple validation pass over all primary config sections.
    Raises ConfigError if any section fails.
    """
    _ = get_model_version()
    _ = get_team_profiles()
    _ = get_spread_total_baselines()
    _ = get_chaos_volatility_thresholds()


if __name__ == "__main__":
    try:
        validate_all()
        print("load_config.py — configuration loaded and validated successfully.")
        print(f"config.MODEL_VERSION = {get_model_version()}")
        print(f"constants.MODEL_VERSION = {get_constants_version()}")
        print(f"Teams configured: {', '.join(get_team_profiles().keys())}")
    except ConfigError as e:
        print(f"Configuration validation FAILED: {e}")
