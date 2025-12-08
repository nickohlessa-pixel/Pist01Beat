"""
Core Pist01 Beat package.

Right now this is a minimal scaffold that:
- Imports a simple matchup engine function
- Wraps it in the Pist01Beat class interface
"""

from .matchup_engine import compute_basic_matchup


class Pist01Beat:
    """
    Super-minimal scaffold for the Pist01 Beat model.
    This is just to prove the package wiring works across multiple files.
    """

    def __init__(self):
        # Simple internal flag/message to confirm initialization
        self.status_message = "Pist01 Beat core online"
        self.version = "0.0.1"

    def predict(self, team_a, team_b):
        """
        Minimal placeholder prediction method.

        Args:
            team_a (str): Team code for team A.
            team_b (str): Team code for team B.

        Returns:
            dict: Simple dict confirming the model is wired up.
        """
        base_result = compute_basic_matchup(team_a, team_b)

        # Add a little extra info from this class
        base_result["engine"] = "basic_matchup"
        base_result["version"] = self.version
        base_result["status"] = self.status_message

        return base_result
