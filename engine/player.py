import random
import numpy as np
from engine.names import random_player_name

# Starters per position, then backups
ROSTER_SLOTS = [
    ("QB", 2), ("RB", 3), ("WR", 4), ("TE", 2),
    ("DE", 3), ("DT", 3), ("LB", 4), ("CB", 3), ("S", 3),
    ("K", 1), ("P", 1),
]

# Hard ceiling on how many seasons any player can ever play.
MAX_CAREER_SEASONS = 25


def random_career_cap():
    """Per-player career length, skewed toward shorter careers. A few
    iron men reach the ceiling; most retire well before. Capped at 25."""
    return int(np.clip(round(np.random.normal(8, 5)), 1, MAX_CAREER_SEASONS))


def generate_roster(team_id, team_overall):
    players = []
    for pos, count in ROSTER_SLOTS:
        for i in range(count):
            base = team_overall if i == 0 else team_overall - 12
            overall = float(np.clip(np.random.normal(base, 8), 35, 99))
            players.append({
                "team_id": team_id,
                "name": random_player_name(),
                "position": pos,
                "overall": round(overall, 1),
                "age": random.randint(21, 35),
            })
    return players
