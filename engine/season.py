import random
import numpy as np
from engine.game import simulate_game
from engine.names import random_player_name
from engine.player import random_career_cap, MAX_CAREER_SEASONS
from data.database import get_conn
import config


def _retire_rate(age):
    if age >= 40: return 1.0
    if age >= 38: return 0.70
    if age >= 35: return 0.35
    if age >= 32: return 0.18
    if age >= 28: return 0.08
    return 0.02


def _age_and_retire(c):
    players = [dict(r) for r in c.execute(
        "SELECT * FROM players WHERE retired=0 OR retired IS NULL"
    ).fetchall()]
    teams = {t["id"]: dict(t) for t in c.execute("SELECT * FROM teams").fetchall()}

    retirements = {}
    for p in players:
        new_age = p["age"] + 1
        new_played = (p["seasons_played"] or 0) + 1   # they just played a season
        cap = p["career_cap"] or MAX_CAREER_SEASONS
        # Retire on the age-based roll OR when the career cap is reached.
        if new_played >= cap or random.random() < _retire_rate(new_age):
            c.execute("UPDATE players SET retired=1, age=?, seasons_played=? WHERE id=?",
                      (new_age, new_played, p["id"]))
            retirements.setdefault(p["team_id"], []).append(p["position"])
        else:
            c.execute("UPDATE players SET age=?, seasons_played=? WHERE id=?",
                      (new_age, new_played, p["id"]))

    for team_id, positions in retirements.items():
        team = teams[team_id]
        base = (team["off_rating"] + team["def_rating"]) / 2
        for pos in positions:
            overall = float(np.clip(np.random.normal(base - 5, 8), 35, 80))
            c.execute(
                "INSERT INTO players (team_id, name, position, overall, age, retired, seasons_played, career_cap) "
                "VALUES (?,?,?,?,?,0,0,?)",
                (team_id, random_player_name(), pos, round(overall, 1),
                 random.randint(21, 23), random_career_cap()),
            )


def generate_schedule(team_ids, weeks):
    schedule = []
    for week in range(1, weeks + 1):
        shuffled = team_ids[:]
        random.shuffle(shuffled)
        for i in range(0, len(shuffled) - 1, 2):
            schedule.append({"week": week, "home": shuffled[i], "away": shuffled[i + 1]})
    return schedule


def _save_game(c, season_id, week, h_id, a_id, result, is_playoff=0, rnd=None):
    """Insert a game plus its full team + player stat lines. Used for both
    regular-season and playoff games."""
    c.execute(
        "INSERT INTO games (season_id, week, home_team_id, away_team_id, home_score, away_score, "
        "is_playoff, playoff_round) VALUES (?,?,?,?,?,?,?,?)",
        (season_id, week, h_id, a_id, result["home_score"], result["away_score"], is_playoff, rnd),
    )
    game_id = c.lastrowid

    for tid, ts in [(h_id, result["home_team_stats"]), (a_id, result["away_team_stats"])]:
        c.execute(
            "INSERT INTO game_team_stats (game_id,team_id,pass_yards,rush_yards,total_yards,"
            "first_downs,third_down_conv,third_down_att,red_zone_conv,red_zone_att,"
            "turnovers,sacks_allowed,penalties,penalty_yards,top_seconds,pass_tds,rush_tds) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (game_id, tid, ts["pass_yards"], ts["rush_yards"], ts["total_yards"],
             ts["first_downs"], ts["third_down_conv"], ts["third_down_att"],
             ts["red_zone_conv"], ts["red_zone_att"], ts["turnovers"],
             ts["sacks_allowed"], ts["penalties"], ts["penalty_yards"],
             ts["top_seconds"], ts["pass_tds"], ts["rush_tds"]),
        )

    for side, tid in [("home", h_id), ("away", a_id)]:
        ps = result[f"{side}_player_stats"]

        for row in ps["qb"]:
            c.execute(
                "INSERT INTO game_qb_stats (game_id,player_id,team_id,completions,attempts,"
                "pass_yards,pass_tds,interceptions,rush_attempts,rush_yards) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (game_id, row["player_id"], tid, row["completions"], row["attempts"],
                 row["pass_yards"], row["pass_tds"], row["interceptions"],
                 row["rush_attempts"], row["rush_yards"]),
            )

        for row in ps["rb"]:
            c.execute(
                "INSERT INTO game_rb_stats (game_id,player_id,team_id,carries,rush_yards,rush_tds,"
                "targets,receptions,rec_yards,rec_tds) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (game_id, row["player_id"], tid, row["carries"], row["rush_yards"],
                 row["rush_tds"], row["targets"], row["receptions"],
                 row["rec_yards"], row["rec_tds"]),
            )

        for row in ps["wr"]:
            c.execute(
                "INSERT INTO game_wr_stats (game_id,player_id,team_id,targets,receptions,"
                "rec_yards,rec_tds) VALUES (?,?,?,?,?,?,?)",
                (game_id, row["player_id"], tid, row["targets"],
                 row["receptions"], row["rec_yards"], row["rec_tds"]),
            )

        for row in ps["def"]:
            c.execute(
                "INSERT INTO game_def_stats (game_id,player_id,team_id,tackles,assists,sacks,"
                "interceptions,forced_fumbles,fumble_recoveries,pass_deflections,tfl) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (game_id, row["player_id"], tid, row["tackles"], row["assists"],
                 row["sacks"], row["interceptions"], row["forced_fumbles"],
                 row["fumble_recoveries"], row["pass_deflections"], row["tfl"]),
            )

        for row in ps["k"]:
            c.execute(
                "INSERT INTO game_k_stats (game_id,player_id,team_id,fg_made,fg_att,fg_long,"
                "xp_made,xp_att) VALUES (?,?,?,?,?,?,?,?)",
                (game_id, row["player_id"], tid, row["fg_made"], row["fg_att"],
                 row["fg_long"], row["xp_made"], row["xp_att"]),
            )

        for row in ps["p"]:
            c.execute(
                "INSERT INTO game_p_stats (game_id,player_id,team_id,punts,punt_yards,inside_20) "
                "VALUES (?,?,?,?,?,?)",
                (game_id, row["player_id"], tid, row["punts"],
                 row["punt_yards"], row["inside_20"]),
            )

    return game_id


# ── POSTSEASON ────────────────────────────────────────────────────────────────

def _team_records(c, season_id):
    """Regular-season W/L/T/PCT/DIFF for every team this season."""
    teams = {t["id"]: dict(t) for t in c.execute("SELECT * FROM teams").fetchall()}
    rec = {tid: {**teams[tid], "W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0} for tid in teams}
    games = c.execute(
        "SELECT home_team_id, away_team_id, home_score, away_score "
        "FROM games WHERE season_id=? AND is_playoff=0", (season_id,)
    ).fetchall()
    for g in games:
        h, a, hs, as_ = g["home_team_id"], g["away_team_id"], g["home_score"], g["away_score"]
        rec[h]["PF"] += hs; rec[h]["PA"] += as_
        rec[a]["PF"] += as_; rec[a]["PA"] += hs
        if hs > as_:
            rec[h]["W"] += 1; rec[a]["L"] += 1
        elif as_ > hs:
            rec[a]["W"] += 1; rec[h]["L"] += 1
        else:
            rec[h]["T"] += 1; rec[a]["T"] += 1
    for r in rec.values():
        gp = (r["W"] + r["L"] + r["T"]) or 1
        r["PCT"] = (r["W"] + r["T"] * 0.5) / gp
        r["DIFF"] = r["PF"] - r["PA"]
    return rec


def _seed_conference(rec, conference):
    """NFL-style: 4 division winners (seeds 1-4 by record), then 3 wild cards."""
    teams = [r for r in rec.values() if r["conference"] == conference]
    div_winners = []
    for div in ["North", "South", "East", "West"]:
        dteams = [t for t in teams if t["division"] == div]
        if dteams:
            dteams.sort(key=lambda r: (r["PCT"], r["DIFF"]), reverse=True)
            div_winners.append(dteams[0])
    div_winners.sort(key=lambda r: (r["PCT"], r["DIFF"]), reverse=True)
    winner_ids = {t["id"] for t in div_winners}
    wildcards = [t for t in teams if t["id"] not in winner_ids]
    wildcards.sort(key=lambda r: (r["PCT"], r["DIFF"]), reverse=True)
    seeds = div_winners[:4] + wildcards[:3]
    for i, t in enumerate(seeds):
        t["seed"] = i + 1
    return seeds


def _play_playoff_game(c, season_id, week, high, low, rnd, team_map, roster_map):
    """Higher seed hosts. Ties are broken in favor of the higher seed."""
    result = simulate_game(
        team_map[high["id"]], team_map[low["id"]],
        roster_map.get(high["id"], []), roster_map.get(low["id"], []),
    )
    if result["home_score"] == result["away_score"]:
        result["home_score"] += 3  # overtime — higher seed prevails
    _save_game(c, season_id, week, high["id"], low["id"], result, 1, rnd)
    return high if result["home_score"] > result["away_score"] else low


def _simulate_conference_bracket(c, season_id, seeds, team_map, roster_map):
    wk = config.WEEKS_PER_SEASON
    # Wild Card round: 2v7, 3v6, 4v5 (seed 1 has a bye)
    wc = [
        _play_playoff_game(c, season_id, wk + 1, seeds[1], seeds[6], "Wild Card", team_map, roster_map),
        _play_playoff_game(c, season_id, wk + 1, seeds[2], seeds[5], "Wild Card", team_map, roster_map),
        _play_playoff_game(c, season_id, wk + 1, seeds[3], seeds[4], "Wild Card", team_map, roster_map),
    ]
    # Divisional: reseed — #1 plays lowest remaining seed; other two meet
    survivors = sorted([seeds[0]] + wc, key=lambda r: r["seed"])
    d1 = _play_playoff_game(c, season_id, wk + 2, survivors[0], survivors[-1], "Divisional", team_map, roster_map)
    d2 = _play_playoff_game(c, season_id, wk + 2, survivors[1], survivors[2], "Divisional", team_map, roster_map)
    # Conference Championship
    finalists = sorted([d1, d2], key=lambda r: r["seed"])
    return _play_playoff_game(c, season_id, wk + 3, finalists[0], finalists[1],
                              "Conf Championship", team_map, roster_map)


def _simulate_playoffs(c, season_id, team_map, roster_map):
    """Returns the champion team_id, or None if there aren't enough teams."""
    rec = _team_records(c, season_id)
    afc = _seed_conference(rec, "AFC")
    nfc = _seed_conference(rec, "NFC")
    if len(afc) < 7 or len(nfc) < 7:
        return None  # not enough teams for a full bracket
    afc_champ = _simulate_conference_bracket(c, season_id, afc, team_map, roster_map)
    nfc_champ = _simulate_conference_bracket(c, season_id, nfc, team_map, roster_map)
    # Super Bowl — higher regular-season PCT hosts (keeps a home edge)
    high, low = ((afc_champ, nfc_champ) if afc_champ["PCT"] >= nfc_champ["PCT"]
                 else (nfc_champ, afc_champ))
    winner = _play_playoff_game(c, season_id, config.WEEKS_PER_SEASON + 4,
                                high, low, "Super Bowl", team_map, roster_map)
    return winner["id"]


def run_season(year):
    conn = get_conn()
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO seasons (year) VALUES (?)", (year,))
    conn.commit()
    season_id = c.execute("SELECT id FROM seasons WHERE year=?", (year,)).fetchone()["id"]

    teams = [dict(r) for r in c.execute("SELECT * FROM teams").fetchall()]
    team_map = {t["id"]: t for t in teams}

    all_players = [dict(r) for r in c.execute(
        "SELECT * FROM players WHERE retired=0 OR retired IS NULL"
    ).fetchall()]
    roster_map = {}
    for p in all_players:
        roster_map.setdefault(p["team_id"], []).append(p)

    schedule = generate_schedule(list(team_map.keys()), config.WEEKS_PER_SEASON)
    for g in schedule:
        h_id, a_id = g["home"], g["away"]
        result = simulate_game(
            team_map[h_id], team_map[a_id],
            roster_map.get(h_id, []), roster_map.get(a_id, []),
        )
        _save_game(c, season_id, g["week"], h_id, a_id, result, 0, None)

    # Postseason (rosters are still active here, before aging/retirement)
    champ_id = _simulate_playoffs(c, season_id, team_map, roster_map)
    if champ_id is not None:
        c.execute("UPDATE seasons SET champion_team_id=? WHERE id=?", (champ_id, season_id))

    _age_and_retire(c)
    conn.commit()
    conn.close()
    return season_id
