"""
Super simple matchup engine stub for Pist01 Beat.

This does NOT do real modeling yet.
It just proves we can call into another file cleanly.
"""

def compute_basic_matchup(team_a: str, team_b: str) -> dict:
    return {
        "status": "basic matchup engine running",
        "team_a": team_a,
        "team_b": team_b,
    }
