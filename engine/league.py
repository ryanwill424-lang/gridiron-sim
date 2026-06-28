import numpy as np
from engine.names import get_team_configs
from engine.player import generate_roster, random_career_cap
from data.database import get_conn
import config


def league_exists():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    conn.close()
    return count > 0


def create_league():
    conn = get_conn()
    c = conn.cursor()

    for tc in get_team_configs(config.NUM_TEAMS):
        off = float(np.clip(np.random.normal(50, 12), 20, 85))
        def_ = float(np.clip(np.random.normal(50, 12), 20, 85))

        c.execute(
            "INSERT INTO teams (city, name, abbreviation, conference, division, off_rating, def_rating) "
            "VALUES (?,?,?,?,?,?,?)",
            (tc["city"], tc["name"], tc["abbreviation"],
             tc["conference"], tc["division"], round(off, 1), round(def_, 1)),
        )
        team_id = c.lastrowid

        for p in generate_roster(team_id, (off + def_) / 2):
            c.execute(
                "INSERT INTO players (team_id, name, position, overall, age, seasons_played, career_cap) "
                "VALUES (?,?,?,?,?,0,?)",
                (team_id, p["name"], p["position"], p["overall"], p["age"], random_career_cap()),
            )

    conn.commit()
    conn.close()
