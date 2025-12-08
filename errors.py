# FILE: errors.py
"""
Custom exceptions for Pist01 Beat v3.4.

These errors allow internal engines (Matchup Engine, Chaos Engine,
Minutes Volatility, Spread/Total Model, PrizePicks Engine, etc.)
to fail gracefully with meaningful error messages.
"""


class Pist01BeatError(Exception):
    """Base exception class for the Pist01 Beat ecosystem."""
    pass


class ConfigError(Pist01BeatError):
    """Raised when config.py contains missing or invalid values."""
    pass


class TeamProfileError(Pist01BeatError):
    """Raised when requesting or loading a team profile that doesn't exist."""
    pass


class CalculationError(Pist01BeatError):
    """Raised when a mathematical operation fails or produces invalid output."""
    pass


class EngineStateError(Pist01BeatError):
    """Raised when required engine inputs or state variables are missing."""
    pass


if __name__ == "__main__":
    print("errors.py loaded — custom exceptions available.")
