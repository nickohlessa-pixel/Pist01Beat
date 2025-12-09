"""
High-level Pist01Beat wrapper.

This is the public interface for the Pist01 Beat v3.4 model.

For now, this is a minimal bootstrap implementation whose ONLY job
is to provide a stable Pist01Beat class that can be imported via:

    from pist01beat import Pist01Beat

Later threads can replace the internals of Pist01Beat.predict()
with the full engine integration without changing the import path.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass
class PredictionResult:
    """
    Minimal structured result for Pist01Beat predictions.

    This matches the general shape we've been using:
    - engine_version: string tag for debugging
    - home_team / away_team: 3-letter codes
    - model_spread / model_total: numeric outputs
    - debug: freeform dict for engine internals
    """
    engine_version: str
    home_team: str
    away_team: str
    model_spread: float
    model_total: float
    debug: Dict[str, Any]


class Pist01Beat:
    """
    High-level model wrapper.

    In this bootstrap version, .predict() returns placeholder
    values with a clear debug block so we can verify wiring.

    Later, we will:
    - import the real engines
    - call them in order
    - populate a real PredictionResult
    without changing the public interface.
    """

    def __init__(self, engine_version: str = "3.4-wrapper-bootstrap"):
        self.engine_version = engine_version

    def predict(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """
        Bootstrap prediction method.

        Returns a dict version of PredictionResult so it's easy to
        serialize, log, or print in tests.
        """
        # Placeholder logic: real engines will replace this.
        # For now we just echo teams and drop in obvious dummy numbers.
        result = PredictionResult(
            engine_version=self.engine_version,
            home_team=home_team,
            away_team=away_team,
            model_spread=0.0,   # TODO: replace with real spread model
            model_total=220.0,  # TODO: replace with real total model
            debug={
                "note": "Bootstrap Pist01Beat.predict placeholder. Engines not yet wired.",
                "home_team": home_team,
                "away_team": away_team,
            },
        )
        return asdict(result)
