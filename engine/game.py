import random
import numpy as np


def _ni(mean, std, lo, hi):
    return int(np.clip(round(np.random.normal(mean, std)), lo, hi))


def _pois(lam):
    return int(np.random.poisson(lam))


def simulate_game(home_team, away_team, home_roster, away_roster):
    h_off = home_team["off_rating"]
    h_def = home_team["def_rating"]
    a_off = away_team["off_rating"]
    a_def = away_team["def_rating"]

    home_exp = 21 + (h_off - a_def) * 0.25 + 2.5
    away_exp = 21 + (a_off - h_def) * 0.25

    home_score = max(0, int(round(np.random.normal(home_exp, 9))))
    away_score = max(0, int(round(np.random.normal(away_exp, 9))))

    if home_score == away_score:
        if random.random() < 0.5:
            home_score += 3
        else:
            away_score += 3

    home_ts = _gen_team_stats(home_score)
    away_ts = _gen_team_stats(away_score)

    home_ps = _gen_player_stats(home_roster, home_ts)
    away_ps = _gen_player_stats(away_roster, away_ts)

    return {
        "home_score": home_score,
        "away_score": away_score,
        "home_team_stats": home_ts,
        "away_team_stats": away_ts,
        "home_player_stats": home_ps,
        "away_player_stats": away_ps,
    }


def _gen_team_stats(score):
    total_tds = max(0, round(score / 7.2))
    pass_tds = round(total_tds * random.uniform(0.5, 0.8))
    rush_tds = max(0, total_tds - pass_tds)

    total_yards = _ni(score * 14 + 40, 45, 80, 600)
    pass_frac = random.uniform(0.52, 0.68)
    pass_yards = _ni(total_yards * pass_frac, 25, 30, 480)
    rush_yards = max(0, total_yards - pass_yards)

    first_downs = _ni(total_yards / 17, 3, 6, 35)
    third_att = _ni(13, 3, 6, 22)
    third_conv = _ni(third_att * 0.40, 2, 0, third_att)
    rz_att = max(0, total_tds + random.randint(0, 2))
    rz_conv = min(rz_att, max(0, round(rz_att * random.uniform(0.5, 0.75))))

    return {
        "pass_yards": pass_yards,
        "rush_yards": rush_yards,
        "total_yards": total_yards,
        "first_downs": first_downs,
        "third_down_conv": third_conv,
        "third_down_att": third_att,
        "red_zone_conv": rz_conv,
        "red_zone_att": rz_att,
        "turnovers": _pois(1.3),
        "sacks_allowed": _pois(2.5),
        "penalties": _ni(6, 2, 1, 14),
        "penalty_yards": _ni(50, 15, 5, 120),
        "top_seconds": _ni(1800, 180, 900, 2700),
        "pass_tds": pass_tds,
        "rush_tds": rush_tds,
    }


def _gen_player_stats(roster, ts):
    by_pos = {}
    for p in roster:
        by_pos.setdefault(p["position"], []).append(p)

    result = {"qb": [], "rb": [], "wr": [], "def": [], "k": [], "p": []}

    # QB
    qbs = by_pos.get("QB", [])
    if qbs:
        qb = qbs[0]
        att = _ni(35, 6, 18, 55)
        comp = round(att * random.uniform(0.52, 0.72))
        rush_att = _ni(4, 3, 0, 10)
        result["qb"].append({
            "player_id": qb["id"], "team_id": qb["team_id"],
            "completions": comp, "attempts": att,
            "pass_yards": ts["pass_yards"], "pass_tds": ts["pass_tds"],
            "interceptions": min(ts["turnovers"], _pois(0.8)),
            "rush_attempts": rush_att,
            "rush_yards": _ni(rush_att * 5, 10, max(-5, rush_att * -2), rush_att * 12),
        })

    # RBs
    rbs = by_pos.get("RB", [])
    splits = [0.70, 0.22, 0.08]
    for i, rb in enumerate(rbs[:3]):
        frac = splits[i]
        carries = _ni(20 * frac, 3, 0, 28)
        rush_yards = round(ts["rush_yards"] * frac * random.uniform(0.85, 1.15))
        rush_tds = round(ts["rush_tds"] * frac)
        rec = _ni(4 * frac + 1, 2, 0, 8)
        result["rb"].append({
            "player_id": rb["id"], "team_id": rb["team_id"],
            "carries": carries, "rush_yards": rush_yards, "rush_tds": rush_tds,
            "targets": rec + random.randint(0, 2), "receptions": rec,
            "rec_yards": _ni(rec * 8, 8, 0, rec * 16 + 1),
            "rec_tds": 1 if random.random() < 0.08 * frac else 0,
        })

    # WR / TE
    wrs = by_pos.get("WR", [])
    tes = by_pos.get("TE", [])
    receivers = wrs[:3] + tes[:1]
    rec_fracs = [0.36, 0.26, 0.16, 0.18, 0.04]
    pass_tds_left = ts["pass_tds"]

    for i, rec in enumerate(receivers):
        frac = rec_fracs[i] if i < len(rec_fracs) else 0.05
        tgt = _ni(ts["pass_yards"] / 10 * frac * 1.2, 2, 0, 14)
        rec_count = round(tgt * random.uniform(0.55, 0.78))
        ypc = random.uniform(10, 16) if i < 3 else random.uniform(7, 13)
        rec_yards = _ni(rec_count * ypc, 12, 0, 200)
        td = 0
        if pass_tds_left > 0 and random.random() < 0.38:
            td = 1
            pass_tds_left -= 1
        result["wr"].append({
            "player_id": rec["id"], "team_id": rec["team_id"],
            "targets": tgt, "receptions": rec_count,
            "rec_yards": rec_yards, "rec_tds": td,
        })

    # Defense
    defenders = (by_pos.get("DE", []) + by_pos.get("DT", []) +
                 by_pos.get("LB", []) + by_pos.get("CB", []) + by_pos.get("S", []))
    d_sacks = _pois(2.5)
    d_ints = _pois(0.8)
    d_pds = _pois(6)
    d_ffs = _pois(0.5)
    d_tfl = _pois(4)
    tackle_pool = random.randint(48, 68)

    sacks_given = 0
    ints_given = 0

    for df in defenders:
        pos = df["position"]
        if pos in ["LB", "S"]:
            tk_frac = random.uniform(0.07, 0.16)
        elif pos == "CB":
            tk_frac = random.uniform(0.04, 0.11)
        else:
            tk_frac = random.uniform(0.03, 0.09)

        tackles = round(tackle_pool * tk_frac)
        assists = round(tackles * random.uniform(0.2, 0.45))

        sack = 0.0
        if pos in ["DE", "DT", "LB"] and sacks_given < d_sacks and random.random() < 0.35:
            sack = round(random.uniform(0.5, 1.0), 1)
            sacks_given += sack

        int_ = 0
        if pos in ["CB", "S", "LB"] and ints_given < d_ints and random.random() < 0.25:
            int_ = 1
            ints_given += 1

        pd = round(d_pds * random.uniform(0, 0.25)) if pos in ["CB", "S"] else 0
        ff = 1 if (d_ffs > 0 and random.random() < 0.15) else 0
        tfl = round(d_tfl * random.uniform(0, 0.22), 1) if pos in ["DE", "DT", "LB"] else 0.0

        result["def"].append({
            "player_id": df["id"], "team_id": df["team_id"],
            "tackles": tackles, "assists": assists, "sacks": sack,
            "interceptions": int_, "forced_fumbles": ff,
            "fumble_recoveries": 1 if random.random() < 0.04 else 0,
            "pass_deflections": pd, "tfl": tfl,
        })

    # Kicker
    ks = by_pos.get("K", [])
    if ks:
        k = ks[0]
        tds = ts["pass_tds"] + ts["rush_tds"]
        fg_att = _ni(2.5, 1.2, 0, 6)
        fg_made = round(fg_att * random.uniform(0.75, 0.95))
        result["k"].append({
            "player_id": k["id"], "team_id": k["team_id"],
            "fg_made": fg_made, "fg_att": fg_att,
            "fg_long": _ni(38, 8, 18, 57),
            "xp_made": tds,
            "xp_att": tds + (1 if random.random() < 0.04 else 0),
        })

    # Punter
    ps = by_pos.get("P", [])
    if ps:
        p = ps[0]
        punts = _ni(4, 2, 0, 10)
        avg = random.uniform(40, 52)
        result["p"].append({
            "player_id": p["id"], "team_id": p["team_id"],
            "punts": punts,
            "punt_yards": round(punts * avg),
            "inside_20": round(punts * random.uniform(0.2, 0.45)),
        })

    return result
