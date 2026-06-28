import time
import random
import streamlit as st
import pandas as pd
from tabulate import tabulate
from data.database import init_db, reset_db, get_conn
from engine.league import create_league, league_exists
from engine.season import run_season
import config

st.set_page_config(page_title="GRIDIRON SIM", layout="wide")
init_db()
if not league_exists():
    create_league()

if "stats_cat" not in st.session_state:
    st.session_state["stats_cat"] = "PASSING"
if "at_cat" not in st.session_state:
    st.session_state["at_cat"] = "PASSING"
if "at_pos" not in st.session_state:
    st.session_state["at_pos"] = "QB"
if "at_worst_pos" not in st.session_state:
    st.session_state["at_worst_pos"] = "QB"
if "po_cat" not in st.session_state:
    st.session_state["po_cat"] = "PASSING"
if "po_at_cat" not in st.session_state:
    st.session_state["po_at_cat"] = "PASSING"
if "active_view" not in st.session_state:
    st.session_state["active_view"] = "SIMULATE"

# ── TERMINAL THEME ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

* { font-family: 'Share Tech Mono', 'Courier New', monospace !important; }

.stApp { background-color: #0a0a0a !important; }

/* General text */
.stApp p, .stApp span, .stApp div, .stApp label,
.stApp h1, .stApp h2, .stApp h3, .stMarkdown {
    color: #00ff41 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: #0a0a0a !important;
    border-bottom: 1px solid #00ff41 !important;
    gap: 0px !important;
}
.stTabs [data-baseweb="tab"] {
    background-color: #0a0a0a !important;
    color: #005a14 !important;
    border: 1px solid #003d0f !important;
    border-bottom: none !important;
    border-radius: 0 !important;
    padding: 4px 18px !important;
}
.stTabs [aria-selected="true"] {
    background-color: #003d0f !important;
    color: #00ff41 !important;
    border-color: #00ff41 !important;
}

/* Buttons */
.stButton > button {
    background-color: #0a0a0a !important;
    color: #00ff41 !important;
    border: 1px solid #00ff41 !important;
    border-radius: 0 !important;
    letter-spacing: 1px;
}
.stButton > button:hover {
    background-color: #003d0f !important;
    color: #00ff41 !important;
    border-color: #00ff41 !important;
}
.stButton > button[kind="primary"] {
    background-color: #003d0f !important;
    border-color: #00ff41 !important;
}

/* Selectbox */
[data-baseweb="select"] > div {
    background-color: #0a0a0a !important;
    border: 1px solid #00ff41 !important;
    border-radius: 0 !important;
    color: #00ff41 !important;
}
[data-baseweb="popover"] ul { background-color: #0d0d0d !important; }
[role="option"] { background-color: #0d0d0d !important; color: #00ff41 !important; }
[role="option"]:hover { background-color: #003d0f !important; }

/* Number input */
[data-baseweb="input"] > div,
[data-baseweb="input"] input {
    background-color: #0a0a0a !important;
    border-color: #00ff41 !important;
    border-radius: 0 !important;
    color: #00ff41 !important;
}
[data-testid="stNumberInputContainer"] button {
    background-color: #0a0a0a !important;
    border-color: #003d0f !important;
    color: #00ff41 !important;
}

/* Radio */
[data-baseweb="radio"] > div { gap: 6px !important; }
[data-testid="stRadio"] label { color: #00ff41 !important; }
[data-testid="stRadio"] [aria-checked="true"] div {
    background-color: #00ff41 !important;
    border-color: #00ff41 !important;
}
[data-testid="stRadio"] [aria-checked="false"] div {
    border-color: #005a14 !important;
    background-color: #0a0a0a !important;
}

/* Dataframe */
[data-testid="stDataFrame"] iframe { border: 1px solid #003d0f !important; }

/* Code blocks */
[data-testid="stCode"] pre,
[data-testid="stCode"],
.stCode pre {
    background-color: #0d0d0d !important;
    color: #00ff41 !important;
    border: 1px solid #1a1a1a !important;
    border-radius: 0 !important;
    padding: 6px 10px !important;
}
/* Hide copy button on code blocks */
[data-testid="stCode"] button { display: none !important; }

/* Info / Warning / Success */
[data-testid="stNotification"],
[data-testid="stAlert"] {
    border-radius: 0 !important;
    border-left: 3px solid #00ff41 !important;
    background-color: #0d0d0d !important;
    color: #00ff41 !important;
}
[data-testid="stAlert"][kind="warning"] {
    border-left-color: #ff6600 !important;
    color: #ff6600 !important;
}
[data-testid="stAlert"][kind="success"] {
    border-left-color: #00ff41 !important;
}

/* Progress */
[data-testid="stProgressBar"] > div { background-color: #0d0d0d !important; }
[data-testid="stProgressBar"] > div > div { background-color: #00ff41 !important; }

/* Caption */
[data-testid="stCaptionContainer"] p { color: #005a14 !important; }

/* Divider */
hr { border-color: #003d0f !important; opacity: 1 !important; }

/* Columns gap */
[data-testid="stHorizontalBlock"] { gap: 8px !important; }

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def get_seasons():
    conn = get_conn()
    rows = conn.execute("SELECT year FROM seasons ORDER BY year DESC").fetchall()
    conn.close()
    return [r["year"] for r in rows]


def get_current_season():
    yrs = get_seasons()
    return yrs[0] if yrs else None


def get_standings(year):
    conn = get_conn()
    teams = [dict(r) for r in conn.execute("SELECT * FROM teams").fetchall()]
    games = [dict(r) for r in conn.execute(
        "SELECT g.* FROM games g JOIN seasons s ON g.season_id=s.id "
        "WHERE s.year=? AND g.is_playoff=0", (year,)
    ).fetchall()]
    conn.close()

    rec = {t["id"]: {**t, "W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0} for t in teams}
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

    df = pd.DataFrame(rec.values())
    games_played = (df["W"] + df["L"] + df["T"]).clip(lower=1)
    df["PCT"] = ((df["W"] + df["T"] * 0.5) / games_played).round(3)
    df["DIFF"] = df["PF"] - df["PA"]
    return df.sort_values(["PCT", "DIFF"], ascending=False)


def passer_rating(comp, att, yds, tds, ints):
    if att == 0:
        return 0.0
    a = min(2.375, max(0, (comp / att - 0.3) / 0.2))
    b = min(2.375, max(0, (yds / att - 3) / 4))
    c = min(2.375, max(0, (tds / att) / 0.05))
    d = min(2.375, max(0, (0.095 - (ints / att)) / 0.04))
    return round((a + b + c + d) / 6 * 100, 1)


def _divider():
    st.code("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", language=None)


def _section(label):
    st.code(f"[ {label.upper()} ]", language=None)


def _cat_picker(key, options):
    cols = st.columns(len(options))
    for i, opt in enumerate(options):
        selected = st.session_state[key] == opt
        label = f"[● {opt}]" if selected else f"[  {opt} ]"
        if cols[i].button(label, key=f"_cp_{key}_{opt}",
                          type="primary" if selected else "secondary",
                          use_container_width=True):
            st.session_state[key] = opt
            st.rerun()
    return st.session_state[key]


def _ranked_table_with_buttons(display_df, key, on_click):
    """Render an ASCII table (terminal style) with a leading rank column, plus
    rows of numbered buttons under it. on_click(i) fires for the i-th row."""
    disp = display_df.reset_index(drop=True).copy()
    disp.insert(0, "#", range(1, len(disp) + 1))
    st.code(tabulate(disp, headers="keys", tablefmt="outline", showindex=False), language=None)
    n = len(disp)
    per_row = 5
    for start in range(0, n, per_row):
        chunk = list(range(start, min(start + per_row, n)))
        cols = st.columns(per_row)
        for j, i in enumerate(chunk):
            if cols[j].button(f"[{i + 1}]", key=f"{key}_{i}", use_container_width=True):
                on_click(i)


def _goto_scoreboard_game(game_id):
    st.session_state["selected_game"] = int(game_id)
    st.session_state["active_view"] = "SCOREBOARD"
    st.rerun()


def _goto_scoreboard_season(year):
    st.session_state.pop("selected_game", None)
    st.session_state["sc_yr"] = int(year)
    st.session_state["sc_week"] = 1
    st.session_state["active_view"] = "SCOREBOARD"
    st.rerun()


def _game_card(aa, away_score, ha, home_score):
    a_win = away_score > home_score
    h_win = home_score > away_score
    tie   = not a_win and not h_win
    a_tag = "WIN" if a_win else "TIE" if tie else "   "
    h_tag = "WIN" if h_win else "TIE" if tie else "   "
    l1 = f"  {aa:<4}  {away_score:>3}  {a_tag}      "
    l2 = f"  {ha:<4}  {home_score:>3}  {h_tag} (H)  "
    w = max(len(l1), len(l2))
    l1 = l1.ljust(w); l2 = l2.ljust(w)
    bar = "─" * w
    return f"┌{bar}┐\n│{l1}│\n│{l2}│\n└{bar}┘"


# ── GAME DETAIL HELPERS ───────────────────────────────────────────────────────
COMMENTATORS = ("JIM", "RANDY")


def _team_stat_tables(conn, game_id, team_id):
    """Return an ordered {category: DataFrame} of this team's stats in one game."""
    p = (game_id, team_id)
    tables = {}

    tables["PASSING"] = pd.read_sql(
        "SELECT pl.name AS Player, q.completions AS CMP, q.attempts AS ATT, "
        "q.pass_yards AS YDS, q.pass_tds AS TD, q.interceptions AS INT, "
        "q.rush_yards AS RushYds FROM game_qb_stats q JOIN players pl ON q.player_id=pl.id "
        "WHERE q.game_id=? AND q.team_id=? ORDER BY YDS DESC", conn, params=p)

    tables["RUSHING"] = pd.read_sql(
        "SELECT pl.name AS Player, r.carries AS CAR, r.rush_yards AS YDS, "
        "r.rush_tds AS TD FROM game_rb_stats r JOIN players pl ON r.player_id=pl.id "
        "WHERE r.game_id=? AND r.team_id=? ORDER BY YDS DESC", conn, params=p)

    wr = pd.read_sql(
        "SELECT pl.name AS Player, 'WR' AS Pos, w.targets AS TGT, w.receptions AS REC, "
        "w.rec_yards AS YDS, w.rec_tds AS TD FROM game_wr_stats w JOIN players pl ON w.player_id=pl.id "
        "WHERE w.game_id=? AND w.team_id=?", conn, params=p)
    rbrec = pd.read_sql(
        "SELECT pl.name AS Player, 'RB' AS Pos, r.targets AS TGT, r.receptions AS REC, "
        "r.rec_yards AS YDS, r.rec_tds AS TD FROM game_rb_stats r JOIN players pl ON r.player_id=pl.id "
        "WHERE r.game_id=? AND r.team_id=? AND r.receptions>0", conn, params=p)
    tables["RECEIVING"] = pd.concat([wr, rbrec]).sort_values("YDS", ascending=False)

    tables["DEFENSE"] = pd.read_sql(
        "SELECT pl.name AS Player, d.tackles AS TKL, d.assists AS AST, "
        "ROUND(d.sacks,1) AS SCK, d.interceptions AS INT, d.pass_deflections AS PD, "
        "d.forced_fumbles AS FF, ROUND(d.tfl,1) AS TFL FROM game_def_stats d "
        "JOIN players pl ON d.player_id=pl.id WHERE d.game_id=? AND d.team_id=? "
        "ORDER BY TKL DESC", conn, params=p)

    tables["KICKING"] = pd.read_sql(
        "SELECT pl.name AS Player, k.fg_made AS FGM, k.fg_att AS FGA, k.fg_long AS LNG, "
        "k.xp_made AS XPM, k.xp_att AS XPA FROM game_k_stats k JOIN players pl ON k.player_id=pl.id "
        "WHERE k.game_id=? AND k.team_id=?", conn, params=p)

    tables["PUNTING"] = pd.read_sql(
        "SELECT pl.name AS Player, pt.punts AS PNT, pt.punt_yards AS YDS, "
        "pt.inside_20 AS IN20 FROM game_p_stats pt JOIN players pl ON pt.player_id=pl.id "
        "WHERE pt.game_id=? AND pt.team_id=?", conn, params=p)

    return tables


def get_game_detail(game_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT g.id, g.week, g.home_score, g.away_score, "
        "g.home_team_id, g.away_team_id, s.year AS year, "
        "ht.city||' '||ht.name AS home_name, ht.abbreviation AS home_abv, "
        "at_.city||' '||at_.name AS away_name, at_.abbreviation AS away_abv "
        "FROM games g JOIN seasons s ON g.season_id=s.id "
        "JOIN teams ht ON g.home_team_id=ht.id JOIN teams at_ ON g.away_team_id=at_.id "
        "WHERE g.id=?", (game_id,)).fetchone()
    if row is None:
        conn.close()
        return None, None, None
    game = dict(row)
    home_tables = _team_stat_tables(conn, game_id, game["home_team_id"])
    away_tables = _team_stat_tables(conn, game_id, game["away_team_id"])
    conn.close()
    return game, home_tables, away_tables


def _scorebox(game):
    aw = game["away_score"] > game["home_score"]
    hw = game["home_score"] > game["away_score"]
    l1 = f"  {game['away_name']:<26} {game['away_score']:>3}  {'< W' if aw else '   '}"
    l2 = f"  {game['home_name']+' (H)':<26} {game['home_score']:>3}  {'< W' if hw else '   '}"
    w = max(len(l1), len(l2))
    l1 = l1.ljust(w); l2 = l2.ljust(w)
    bar = "═" * w
    return f"╔{bar}╗\n║{l1}║\n║{l2}║\n╚{bar}╝"


# ── ASCII figure animation ────────────────────────────────────────────────────
# Each frame is a list of text lines describing a detailed football player.
# Frames are normalized per-animation, then centered + grounded inside a
# fixed BOX_W x BOX_H bordered canvas so the box never moves.

BOX_W, BOX_H = 40, 16   # total size incl. border

# Shared body parts for the runner (helmet, facemask, shoulder pads, jersey #8).
_HEAD  = [" .---. ", "(o |== ", " \\---/ "]   # domed helmet w/ facemask
_NECK  = "   |||  "
_SHLD  = "  /===\\ "
_CHEST = "  | 8 | "
_WAIST = "  |___| "

_ARM_R = "  /=+=o "   # right fist driving up
_ARM_L = "  o=+=\\ "   # left fist driving up

_LEG_A = ["  / \\  ", " /   \\ ", "/     |"]   # open stride
_LEG_B = ["  |\\   ", "  | \\  ", "  |  \\ "]    # trail leg back
_LEG_C = ["  /|   ", " / |   ", "/  |   "]      # lead leg forward
_LEG_S = ["  | |  ", "  | |  ", "  | |  "]      # planted/upright


def _runner(arm, legs):
    return _HEAD + [_NECK, _SHLD, arm, _CHEST, _WAIST] + legs


_RUN = [
    _runner(_ARM_R, _LEG_A),
    _runner(_ARM_L, _LEG_B),
    _runner(_ARM_R, _LEG_C),
    _runner(_ARM_L, _LEG_A),
]

# Arms thrown up, ball spiked overhead.
_TD_CEL = [
    [" \\o   o/", "  \\===/ ", "  | 8 | ", "  |___| ", "  | | | ", "  | | | ", "  / \\  "],
    ["o \\   / o", "  \\===/ ", "  | 8 | ", "  |___| ", "  | | | ", "  / | \\ ", " /   \\ "],
    ["\\\\o o//", "  \\===/ ", "  | 8 | ", "  |___| ", "  | | | ", "  | | | ", " /   \\ "],
]

# Leap to high-point the ball: reach, secure, land holding it.
_LEAP_REACH = [
    "   _o_  ", "  \\   / ", "   | |  ", " .---. ", "(o |== ",
    " \\---/ ", "  | 8 | ", "  |___| ", "  | |  ", " /   \\ ",
]
_LEAP_CATCH = [
    "   ( ) ", "  (o o) ", "  \\| |/ ", " .---. ", "(o |== ",
    " \\---/ ", "  | 8 | ", "  |___| ", "  | |  ", " /   \\ ",
]
_LAND_HOLD = [
    " .---. ", "(o |== ", " \\---/ ", "   |||  ", "  /===\\ ",
    "  | 8 |(o)", "  |___| ", "  | |  ", "  / \\  ", " /   \\ ",
]
_DROP_END = [
    " .---. ", "(o |== ", " \\---/ ", "   |||  ", "  /===\\ ",
    "  /=+=\\ ", "  |___| ", "  | |  ", "  / \\ o", " /   \\ ",
]

_CATCH = [_LEAP_REACH, _LEAP_CATCH, _LAND_HOLD]   # successful grab
_DROP  = [_LEAP_REACH, _DROP_END]                 # ball gets away

# Plant, swing the leg, ball launches up and away.
_KICK = [
    [" .---. ", "(o |== ", " \\---/ ", "   |||  ", "  /===\\ ",
     "  | 8 | ", "  |___| ", "  | |  ", "  | \\  ", " _|  (o)"],
    [" .---.  o", "(o |==   ", " \\---/   ", "   |||    ", "  /===\\  ",
     "  | 8 |  ", "  |___|  ", "  |__    ", "  |  \\__ ", " _|      "],
    [" .---.      o", "(o |==       ", " \\---/       ", "   |||        ", "  /===\\      ",
     "  | 8 |      ", "  |__\\       ", "  |   \\      ", "  |    \\     ", " _|          "],
]

# Ball-carrier (left, #8) meets a defender (right, #5); carrier goes down.
_TACKLE = [
    [" .---.        .---. ", "(o |==       ==| o)", " \\---/        \\---/ ",
     "   |||          |||  ", "  /===\\        /===\\ ", "  | 8 |        | 5 | ",
     "  |___|        |___| ", "  | | |        | | | ", "  / \\          / \\  ", " /   \\        /   \\ "],
    [" .---.    .---. ", "(o |==   ==| o)", " \\---/    \\---/ ",
     "   |||  ||  |||  ", "  /===\\/==\\/===\\ ", "  | 8 X 8 X 5 | ", "  |___|__|___| ",
     "  | |    | | | ", "  /\\      /\\  ", " /  \\    /  \\ "],
    ["            .---. ", "           ==| o)", "            \\---/ ",
     "   _____      |||  ", " .(o ===\\    /===\\ ", " '------'    | 5 | ",
     "             |___| ", "             | | | ", " ___________ / \\  ", "############/   \\#"],
]


def _norm(frames):
    """Pad every frame in one animation to a shared width/height."""
    h = max(len(f) for f in frames)
    w = max(max(len(line) for line in f) for f in frames)
    out = []
    for f in frames:
        padded = list(f) + [""] * (h - len(f))
        out.append("\n".join(line.ljust(w) for line in padded))
    return out


def _frame_box(frame_str):
    """Center + ground a (normalized) frame inside the fixed BOX_W x BOX_H
    bordered canvas. Returns a string of exactly BOX_H rows x BOX_W cols."""
    iw, ih = BOX_W - 2, BOX_H - 2
    lines = frame_str.split("\n")
    h = len(lines)
    w = max(len(ln) for ln in lines)
    left = max(0, (iw - w) // 2)
    content_rows = ih - 1                 # last inner row is the ground
    top = max(0, content_rows - h)
    rows = []
    for r in range(ih):
        if r == ih - 1:
            rows.append("‾" * iw)
        else:
            fi = r - top
            if 0 <= fi < h:
                rows.append((" " * left + lines[fi]).ljust(iw)[:iw])
            else:
                rows.append(" " * iw)
    top_b = "╔" + "═" * iw + "╗"
    bot_b = "╚" + "═" * iw + "╝"
    return "\n".join([top_b] + ["║" + r + "║" for r in rows] + [bot_b])


def _play_result(rng):
    results = [
        ("TOUCHDOWN",   22),
        ("TACKLE",      40),
        ("INCOMPLETE",  18),
        ("FIELD GOAL",  12),
        ("FUMBLE",       8),
    ]
    total = sum(wt for _, wt in results)
    pick = rng.uniform(0, total)
    acc = 0
    for name, wt in results:
        acc += wt
        if pick <= acc:
            return name
    return results[0][0]


def _build_sequence(result):
    """Return (list_of_boxed_frame_strings, caption) for a result."""
    if result == "TOUCHDOWN":
        raw, cap = _RUN * 2 + _CATCH + _TD_CEL, "TOUCHDOWN!!!"
    elif result == "FIELD GOAL":
        raw, cap = [_KICK[0], _KICK[0], _KICK[1], _KICK[2], _KICK[2]], "FIELD GOAL IS GOOD!"
    elif result == "INCOMPLETE":
        raw, cap = _RUN[:3] + _DROP, "INCOMPLETE — DROPPED!"
    elif result == "FUMBLE":
        raw, cap = _RUN[:2] + _TACKLE, "FUMBLE!!!"
    else:  # TACKLE / short gain
        raw, cap = _RUN * 2 + _TACKLE, "TACKLED SHORT"
    frames = [_frame_box(f) for f in _norm(raw)]
    return frames, cap


def _all_player_names(home_tables, away_tables):
    names = []
    for tables in (home_tables, away_tables):
        for df in tables.values():
            if not df.empty:
                names.extend(df["Player"].tolist())
    return names or ["A player"]


def generate_commentary(game, home_tables, away_tables, rng):
    aw = game["away_score"] > game["home_score"]
    winner = game["away_name"] if aw else game["home_name"]
    loser = game["home_name"] if aw else game["away_name"]
    wscore = max(game["home_score"], game["away_score"])
    lscore = min(game["home_score"], game["away_score"])

    def leader(tables_a, tables_b, cat, col):
        rows = []
        for t in (tables_a, tables_b):
            df = t.get(cat)
            if df is not None and not df.empty:
                rows.append(df.iloc[0])
        if not rows:
            return None
        return max(rows, key=lambda r: r[col])

    lines = []

    def say(text, breaking=False):
        who = COMMENTATORS[len(lines) % 2]
        prefix = ">>> BREAKING: " if breaking else ""
        lines.append(f"{who}: {prefix}{text}")

    say(f"Welcome to {game['away_abv']} at {game['home_abv']}, "
        f"Week {game['week']} of the {game['year']} season!")
    if lscore == wscore:
        say(f"And it ends in a deadlock — {wscore} apiece. Incredible.")
    else:
        say(f"Final score: {winner} {wscore}, {loser} {lscore}.")

    passer = leader(home_tables, away_tables, "PASSING", "YDS")
    if passer is not None and passer["YDS"] > 0:
        say(f"{passer['Player']} carved up the secondary — {int(passer['YDS'])} "
            f"yards and {int(passer['TD'])} TD through the air.")

    rusher = leader(home_tables, away_tables, "RUSHING", "YDS")
    if rusher is not None and rusher["YDS"] > 0:
        say(f"On the ground, {rusher['Player']} was a workhorse: "
            f"{int(rusher['CAR'])} carries for {int(rusher['YDS'])}.")

    receiver = leader(home_tables, away_tables, "RECEIVING", "YDS")
    if receiver is not None and receiver["YDS"] > 0:
        say(f"{receiver['Player']} could not be covered — "
            f"{int(receiver['REC'])} grabs, {int(receiver['YDS'])} yards.")

    defender = leader(home_tables, away_tables, "DEFENSE", "TKL")
    if defender is not None and defender["TKL"] > 0:
        say(f"Defensively, {defender['Player']} was everywhere — "
            f"{int(defender['TKL'])} tackles, {defender['SCK']} sacks.")

    margin = wscore - lscore
    if margin == 0:
        say("Two teams that simply refused to lose.")
    elif margin <= 3:
        say("Came right down to the wire — a one-possession thriller.")
    elif margin >= 28:
        say(f"This one got ugly. A {margin}-point demolition.")
    else:
        say("A solid, hard-fought ballgame from both sides.")

    # ── Rare events engine (seeded — each game has a fixed fate) ──
    r = rng.random()
    name = rng.choice(_all_player_names(home_tables, away_tables))
    if r < 0.001:
        cosmic = rng.choice([
            "a small plane just buzzed the stadium and dipped a wing at midfield",
            "a total solar eclipse fell over the field mid-snap — pitch black",
            "a meteor streaked across the sky and the whole crowd gasped",
            "the scoreboard started speaking in tongues for a full minute",
        ])
        say(f"You are NOT going to believe this — {cosmic}!", breaking=True)
        say("Randy, I have called football for thirty years and never seen that.")
    elif r < 0.011:
        odd = rng.choice([
            "a streaker just bolted across the 50 in a chicken costume",
            "the stadium lights flickered and half the crowd lost power",
            "a rogue hot dog cannon misfired into the upper deck",
        ])
        say(f"And — {odd}. Security is on the move.", breaking=True)
    elif r < 0.061:
        say(f"Oh, and {name} limped off after that one — looks like a tweaked "
            f"ankle. Nothing serious, walking it off.")

    say("That's the ballgame. Thanks for joining us — goodnight, everybody!")
    return lines


def render_game_detail(game_id):
    game, home_tables, away_tables = get_game_detail(game_id)
    if game is None:
        st.info("GAME NOT FOUND.")
        st.session_state.pop("selected_game", None)
        return

    if st.button("<< BACK TO SCOREBOARD", key="back_to_sb"):
        st.session_state.pop("selected_game", None)
        st.rerun()

    _section(f"WEEK {game['week']} — SEASON {game['year']}")
    st.code(_scorebox(game), language=None)

    # ── Play animation ──
    _section("play of the game")
    result = _play_result(random.Random(game_id))
    frames, caption = _build_sequence(result)
    field_ph = st.empty()
    field_ph.code(frames[0] + "\n  ▶ READY — PRESS PLAY", language=None)
    if st.button("► PLAY", key=f"play_{game_id}", type="primary"):
        for i, fr in enumerate(frames):
            last = i == len(frames) - 1
            tag = f"  ▶ {caption}" if last else "  ▶ ..."
            field_ph.code(fr + "\n" + tag, language=None)
            time.sleep(0.12)

    # ── Commentary ──
    _section("booth commentary")
    lines = generate_commentary(game, home_tables, away_tables, random.Random(game_id))
    st.code("\n".join(lines), language=None)

    # ── Player stats ──
    _divider()
    for side_abv, tables in [(game["away_abv"], away_tables), (game["home_abv"], home_tables)]:
        _section(f"{side_abv} player stats")
        any_rows = False
        for cat, df in tables.items():
            if df is not None and not df.empty:
                any_rows = True
                st.code(f"  -- {cat} --", language=None)
                st.code(tabulate(df, headers="keys", tablefmt="outline", showindex=False),
                        language=None)
        if not any_rows:
            st.code("  (no recorded stats)", language=None)


def _render_team_cards(df, team_id):
    """Render a team's games as cards with a per-team W/L/T result + view button."""
    if df.empty:
        st.code("  (no games)", language=None)
        return
    cols = st.columns(4)
    for i, (_, g) in enumerate(df.iterrows()):
        is_home = g["home_team_id"] == team_id
        tf = g["home_score"] if is_home else g["away_score"]
        ta = g["away_score"] if is_home else g["home_score"]
        res = "W" if tf > ta else "L" if ta > tf else "T"
        label = g["playoff_round"] if g["is_playoff"] else f"WK {int(g['week'])}"
        with cols[i % 4]:
            st.code(f"  {label}  [{res}]\n" +
                    _game_card(g["aa"], g["away_score"], g["ha"], g["home_score"]), language=None)
            if st.button("VIEW GAME", key=f"tview_{int(g['gid'])}", use_container_width=True):
                st.session_state["selected_game"] = int(g["gid"])
                st.rerun()


def render_team_games(conn, team_id):
    """Season selector + that team's games (regular season, then playoffs)."""
    team = conn.execute(
        "SELECT city||' '||name AS full, abbreviation AS abv FROM teams WHERE id=?", (team_id,)
    ).fetchone()
    tyears = [r["year"] for r in conn.execute(
        "SELECT DISTINCT s.year FROM games g JOIN seasons s ON g.season_id=s.id "
        "WHERE g.home_team_id=? OR g.away_team_id=? ORDER BY s.year DESC", (team_id, team_id)
    ).fetchall()]
    if not tyears:
        st.info(f"{team['full']} HAS NO GAMES YET.")
        return

    yr = st.selectbox("SEASON", tyears, key="sc_team_yr")
    games = pd.read_sql("""
        SELECT g.id AS gid, g.week, g.is_playoff, g.playoff_round,
               g.home_team_id, g.away_team_id, g.home_score, g.away_score,
               ht.abbreviation AS ha, at_.abbreviation AS aa
        FROM games g JOIN seasons s ON g.season_id=s.id
        JOIN teams ht ON g.home_team_id=ht.id JOIN teams at_ ON g.away_team_id=at_.id
        WHERE s.year=? AND (g.home_team_id=? OR g.away_team_id=?)
        ORDER BY g.is_playoff, g.week
    """, conn, params=(yr, team_id, team_id))

    reg = games[games["is_playoff"] == 0]
    W = L = T = PF = PA = 0
    for _, g in reg.iterrows():
        is_home = g["home_team_id"] == team_id
        tf = g["home_score"] if is_home else g["away_score"]
        ta = g["away_score"] if is_home else g["home_score"]
        PF += tf; PA += ta
        if tf > ta: W += 1
        elif ta > tf: L += 1
        else: T += 1
    diff = PF - PA
    st.code(f"  {team['full']} — {yr} season: {W}-{L}-{T}, "
            f"{'+' if diff >= 0 else ''}{diff} diff", language=None)

    _section(f"{team['abv']} — {yr} games")
    _render_team_cards(reg, team_id)

    po = games[games["is_playoff"] == 1]
    if not po.empty:
        _section(f"{team['abv']} — {yr} playoffs")
        _render_team_cards(po, team_id)


# ── WORST-PLAYER QUERIES (ALL-TIME) ───────────────────────────────────────────
# "Worst" = worst efficiency metric among players who meet a minimum career
# volume, so a one-snap bench player can't trivially be the worst.

def _worst_by_position(conn, pos):
    if pos == "QB":
        df = pd.read_sql("""
            SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
                   SUM(q.completions) AS CMP, SUM(q.attempts) AS ATT, SUM(q.pass_yards) AS YDS,
                   SUM(q.pass_tds) AS TD, SUM(q.interceptions) AS INT
            FROM game_qb_stats q JOIN players p ON q.player_id=p.id JOIN teams t ON q.team_id=t.id
            JOIN games g ON q.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
            WHERE p.position='QB' GROUP BY q.player_id HAVING SUM(q.attempts)>=100
        """, conn)
        if df.empty:
            return df
        df["RTG"] = df.apply(lambda r: passer_rating(r.CMP, r.ATT, r.YDS, r.TD, r.INT), axis=1)
        return df.sort_values("RTG").head(25)[["Player", "Team", "Seasons", "CMP", "ATT", "YDS", "TD", "INT", "RTG"]]

    if pos == "RB":
        df = pd.read_sql("""
            SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
                   SUM(r.carries) AS CAR, SUM(r.rush_yards) AS YDS, SUM(r.rush_tds) AS TD
            FROM game_rb_stats r JOIN players p ON r.player_id=p.id JOIN teams t ON r.team_id=t.id
            JOIN games g ON r.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
            WHERE p.position='RB' GROUP BY r.player_id HAVING SUM(r.carries)>=100
        """, conn)
        if df.empty:
            return df
        df["YPC"] = (df["YDS"] / df["CAR"].clip(1)).round(2)
        return df.sort_values("YPC").head(25)[["Player", "Team", "Seasons", "CAR", "YDS", "YPC", "TD"]]

    if pos in ("WR", "TE"):
        df = pd.read_sql("""
            SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
                   SUM(w.targets) AS TGT, SUM(w.receptions) AS REC, SUM(w.rec_yards) AS YDS,
                   SUM(w.rec_tds) AS TD
            FROM game_wr_stats w JOIN players p ON w.player_id=p.id JOIN teams t ON w.team_id=t.id
            JOIN games g ON w.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
            WHERE p.position=? GROUP BY w.player_id HAVING SUM(w.targets)>=50
        """, conn, params=(pos,))
        if df.empty:
            return df
        df["YPR"] = (df["YDS"] / df["REC"].clip(1)).round(2)
        return df.sort_values("YPR").head(25)[["Player", "Team", "Seasons", "TGT", "REC", "YDS", "YPR", "TD"]]

    if pos in ("DE", "DT", "LB", "CB", "S"):
        df = pd.read_sql("""
            SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
                   SUM(d.tackles) AS TKL, SUM(d.assists) AS AST, ROUND(SUM(d.sacks),1) AS SCK
            FROM game_def_stats d JOIN players p ON d.player_id=p.id JOIN teams t ON d.team_id=t.id
            JOIN games g ON d.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
            WHERE p.position=? GROUP BY d.player_id HAVING COUNT(DISTINCT s.id)>=2
        """, conn, params=(pos,))
        if df.empty:
            return df
        df["TKL/SEAS"] = (df["TKL"] / df["Seasons"].clip(1)).round(1)
        return df.sort_values("TKL/SEAS").head(25)[["Player", "Team", "Seasons", "TKL", "AST", "SCK", "TKL/SEAS"]]

    if pos == "K":
        df = pd.read_sql("""
            SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
                   SUM(k.fg_made) AS FGM, SUM(k.fg_att) AS FGA, MAX(k.fg_long) AS LNG
            FROM game_k_stats k JOIN players p ON k.player_id=p.id JOIN teams t ON k.team_id=t.id
            JOIN games g ON k.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
            WHERE p.position='K' GROUP BY k.player_id HAVING SUM(k.fg_att)>=20
        """, conn)
        if df.empty:
            return df
        df["FG%"] = (df["FGM"] / df["FGA"].clip(1) * 100).round(1)
        return df.sort_values("FG%").head(25)[["Player", "Team", "Seasons", "FGM", "FGA", "FG%", "LNG"]]

    # P
    df = pd.read_sql("""
        SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
               SUM(pt.punts) AS PNT, SUM(pt.punt_yards) AS YDS, SUM(pt.inside_20) AS IN20
        FROM game_p_stats pt JOIN players p ON pt.player_id=p.id JOIN teams t ON pt.team_id=t.id
        JOIN games g ON pt.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
        WHERE p.position='P' GROUP BY pt.player_id HAVING SUM(pt.punts)>=20
    """, conn)
    if df.empty:
        return df
    df["AVG"] = (df["YDS"] / df["PNT"].clip(1)).round(1)
    return df.sort_values("AVG").head(25)[["Player", "Team", "Seasons", "PNT", "YDS", "AVG", "IN20"]]


def _worst_overall(conn):
    """One worst-qualifying-player row per category, league-wide."""
    rows = []

    qb = pd.read_sql("""
        SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
               SUM(q.completions) AS CMP, SUM(q.attempts) AS ATT, SUM(q.pass_yards) AS YDS,
               SUM(q.pass_tds) AS TD, SUM(q.interceptions) AS INT
        FROM game_qb_stats q JOIN players p ON q.player_id=p.id JOIN teams t ON q.team_id=t.id
        JOIN games g ON q.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
        WHERE p.position='QB' GROUP BY q.player_id HAVING SUM(q.attempts)>=100
    """, conn)
    if not qb.empty:
        qb["RTG"] = qb.apply(lambda r: passer_rating(r.CMP, r.ATT, r.YDS, r.TD, r.INT), axis=1)
        w = qb.sort_values("RTG").iloc[0]
        rows.append(["PASSING", w.Player, w.Team, int(w.Seasons), "RTG", w.RTG, f"{int(w.ATT)} att"])

    rb = pd.read_sql("""
        SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
               SUM(r.carries) AS CAR, SUM(r.rush_yards) AS YDS
        FROM game_rb_stats r JOIN players p ON r.player_id=p.id JOIN teams t ON r.team_id=t.id
        JOIN games g ON r.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
        WHERE p.position='RB' GROUP BY r.player_id HAVING SUM(r.carries)>=100
    """, conn)
    if not rb.empty:
        rb["YPC"] = (rb["YDS"] / rb["CAR"].clip(1)).round(2)
        w = rb.sort_values("YPC").iloc[0]
        rows.append(["RUSHING", w.Player, w.Team, int(w.Seasons), "YPC", w.YPC, f"{int(w.CAR)} car"])

    rec = pd.read_sql("""
        SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
               SUM(w.targets) AS TGT, SUM(w.receptions) AS REC, SUM(w.rec_yards) AS YDS
        FROM game_wr_stats w JOIN players p ON w.player_id=p.id JOIN teams t ON w.team_id=t.id
        JOIN games g ON w.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
        WHERE p.position IN ('WR','TE') GROUP BY w.player_id HAVING SUM(w.targets)>=50
    """, conn)
    if not rec.empty:
        rec["YPR"] = (rec["YDS"] / rec["REC"].clip(1)).round(2)
        w = rec.sort_values("YPR").iloc[0]
        rows.append(["RECEIVING", w.Player, w.Team, int(w.Seasons), "YPR", w.YPR, f"{int(w.TGT)} tgt"])

    dfn = pd.read_sql("""
        SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
               SUM(d.tackles) AS TKL
        FROM game_def_stats d JOIN players p ON d.player_id=p.id JOIN teams t ON d.team_id=t.id
        JOIN games g ON d.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
        GROUP BY d.player_id HAVING COUNT(DISTINCT s.id)>=2
    """, conn)
    if not dfn.empty:
        dfn["TPS"] = (dfn["TKL"] / dfn["Seasons"].clip(1)).round(1)
        w = dfn.sort_values("TPS").iloc[0]
        rows.append(["DEFENSE", w.Player, w.Team, int(w.Seasons), "TKL/SEAS", w.TPS, f"{int(w.TKL)} tkl"])

    k = pd.read_sql("""
        SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
               SUM(k.fg_made) AS FGM, SUM(k.fg_att) AS FGA
        FROM game_k_stats k JOIN players p ON k.player_id=p.id JOIN teams t ON k.team_id=t.id
        JOIN games g ON k.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
        GROUP BY k.player_id HAVING SUM(k.fg_att)>=20
    """, conn)
    if not k.empty:
        k["FG%"] = (k["FGM"] / k["FGA"].clip(1) * 100).round(1)
        w = k.sort_values("FG%").iloc[0]
        rows.append(["KICKING", w.Player, w.Team, int(w.Seasons), "FG%", w["FG%"], f"{int(w.FGA)} fga"])

    p = pd.read_sql("""
        SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
               SUM(pt.punts) AS PNT, SUM(pt.punt_yards) AS YDS
        FROM game_p_stats pt JOIN players p ON pt.player_id=p.id JOIN teams t ON pt.team_id=t.id
        JOIN games g ON pt.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
        GROUP BY pt.player_id HAVING SUM(pt.punts)>=20
    """, conn)
    if not p.empty:
        p["AVG"] = (p["YDS"] / p["PNT"].clip(1)).round(1)
        w = p.sort_values("AVG").iloc[0]
        rows.append(["PUNTING", w.Player, w.Team, int(w.Seasons), "AVG", w.AVG, f"{int(w.PNT)} pnt"])

    return pd.DataFrame(rows, columns=["Category", "Player", "Team", "Seasons", "Metric", "Value", "Volume"])


# ── POSTSEASON STAT QUERIES ───────────────────────────────────────────────────
PLAYOFF_ROUNDS = ["Wild Card", "Divisional", "Conf Championship", "Super Bowl"]


def _postseason_leaders(conn, cat, year=None):
    """Best postseason stat leaders (is_playoff=1). year=None -> all-time."""
    yc = " AND s.year=? " if year is not None else ""
    pr = (year,) if year is not None else ()

    if cat == "PASSING":
        df = pd.read_sql(f"""
            SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT g.id) AS GP,
                   SUM(q.completions) AS CMP, SUM(q.attempts) AS ATT, SUM(q.pass_yards) AS YDS,
                   SUM(q.pass_tds) AS TD, SUM(q.interceptions) AS INT
            FROM game_qb_stats q JOIN players p ON q.player_id=p.id JOIN teams t ON q.team_id=t.id
            JOIN games g ON q.game_id=g.id AND g.is_playoff=1 JOIN seasons s ON g.season_id=s.id
            WHERE 1=1 {yc} GROUP BY q.player_id ORDER BY YDS DESC LIMIT 25
        """, conn, params=pr)
        if not df.empty:
            df["RTG"] = df.apply(lambda r: passer_rating(r.CMP, r.ATT, r.YDS, r.TD, r.INT), axis=1)
            df = df[["Player", "Team", "GP", "CMP", "ATT", "YDS", "TD", "INT", "RTG"]]
        return df

    if cat == "RUSHING":
        df = pd.read_sql(f"""
            SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT g.id) AS GP,
                   SUM(r.carries) AS CAR, SUM(r.rush_yards) AS YDS, SUM(r.rush_tds) AS TD
            FROM game_rb_stats r JOIN players p ON r.player_id=p.id JOIN teams t ON r.team_id=t.id
            JOIN games g ON r.game_id=g.id AND g.is_playoff=1 JOIN seasons s ON g.season_id=s.id
            WHERE 1=1 {yc} GROUP BY r.player_id ORDER BY YDS DESC LIMIT 25
        """, conn, params=pr)
        if not df.empty:
            df["YPC"] = (df["YDS"] / df["CAR"].clip(1)).round(2)
            df = df[["Player", "Team", "GP", "CAR", "YDS", "YPC", "TD"]]
        return df

    if cat == "RECEIVING":
        wr = pd.read_sql(f"""
            SELECT p.name AS Player, t.abbreviation AS Team, p.position AS Pos, COUNT(DISTINCT g.id) AS GP,
                   SUM(w.targets) AS TGT, SUM(w.receptions) AS REC, SUM(w.rec_yards) AS YDS, SUM(w.rec_tds) AS TD
            FROM game_wr_stats w JOIN players p ON w.player_id=p.id JOIN teams t ON w.team_id=t.id
            JOIN games g ON w.game_id=g.id AND g.is_playoff=1 JOIN seasons s ON g.season_id=s.id
            WHERE 1=1 {yc} GROUP BY w.player_id
        """, conn, params=pr)
        rb = pd.read_sql(f"""
            SELECT p.name AS Player, t.abbreviation AS Team, 'RB' AS Pos, COUNT(DISTINCT g.id) AS GP,
                   SUM(r.targets) AS TGT, SUM(r.receptions) AS REC, SUM(r.rec_yards) AS YDS, SUM(r.rec_tds) AS TD
            FROM game_rb_stats r JOIN players p ON r.player_id=p.id JOIN teams t ON r.team_id=t.id
            JOIN games g ON r.game_id=g.id AND g.is_playoff=1 JOIN seasons s ON g.season_id=s.id
            WHERE 1=1 {yc} GROUP BY r.player_id
        """, conn, params=pr)
        df = pd.concat([wr, rb]).sort_values("YDS", ascending=False).head(25)
        if not df.empty:
            df = df[["Player", "Team", "Pos", "GP", "TGT", "REC", "YDS", "TD"]]
        return df

    if cat == "DEFENSE":
        return pd.read_sql(f"""
            SELECT p.name AS Player, t.abbreviation AS Team, p.position AS Pos, COUNT(DISTINCT g.id) AS GP,
                   SUM(d.tackles) AS TKL, SUM(d.assists) AS AST, ROUND(SUM(d.sacks),1) AS SCK,
                   SUM(d.interceptions) AS INT, SUM(d.forced_fumbles) AS FF
            FROM game_def_stats d JOIN players p ON d.player_id=p.id JOIN teams t ON d.team_id=t.id
            JOIN games g ON d.game_id=g.id AND g.is_playoff=1 JOIN seasons s ON g.season_id=s.id
            WHERE 1=1 {yc} GROUP BY d.player_id ORDER BY TKL DESC LIMIT 25
        """, conn, params=pr)

    if cat == "KICKING":
        df = pd.read_sql(f"""
            SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT g.id) AS GP,
                   SUM(k.fg_made) AS FGM, SUM(k.fg_att) AS FGA, MAX(k.fg_long) AS LNG, SUM(k.xp_made) AS XPM
            FROM game_k_stats k JOIN players p ON k.player_id=p.id JOIN teams t ON k.team_id=t.id
            JOIN games g ON k.game_id=g.id AND g.is_playoff=1 JOIN seasons s ON g.season_id=s.id
            WHERE 1=1 {yc} GROUP BY k.player_id ORDER BY FGM DESC LIMIT 25
        """, conn, params=pr)
        if not df.empty:
            df["FG%"] = (df["FGM"] / df["FGA"].clip(1) * 100).round(1)
            df = df[["Player", "Team", "GP", "FGM", "FGA", "FG%", "LNG", "XPM"]]
        return df

    # PUNTING
    df = pd.read_sql(f"""
        SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT g.id) AS GP,
               SUM(pt.punts) AS PNT, SUM(pt.punt_yards) AS YDS, SUM(pt.inside_20) AS IN20
        FROM game_p_stats pt JOIN players p ON pt.player_id=p.id JOIN teams t ON pt.team_id=t.id
        JOIN games g ON pt.game_id=g.id AND g.is_playoff=1 JOIN seasons s ON g.season_id=s.id
        WHERE 1=1 {yc} GROUP BY pt.player_id ORDER BY YDS DESC LIMIT 25
    """, conn, params=pr)
    if not df.empty:
        df["AVG"] = (df["YDS"] / df["PNT"].clip(1)).round(1)
        df = df[["Player", "Team", "GP", "PNT", "YDS", "AVG", "IN20"]]
    return df


def _playoff_team_records(conn):
    df = pd.read_sql("""
        SELECT t.city||' '||t.name AS Team, t.abbreviation AS ABV,
               (SELECT COUNT(*) FROM seasons s WHERE s.champion_team_id=t.id) AS Titles,
               SUM(CASE WHEN (g.home_team_id=t.id AND g.home_score>g.away_score)
                             OR (g.away_team_id=t.id AND g.away_score>g.home_score) THEN 1 ELSE 0 END) AS W,
               SUM(CASE WHEN (g.home_team_id=t.id AND g.home_score<g.away_score)
                             OR (g.away_team_id=t.id AND g.away_score<g.home_score) THEN 1 ELSE 0 END) AS L,
               COUNT(*) AS GP
        FROM teams t JOIN games g ON (g.home_team_id=t.id OR g.away_team_id=t.id) AND g.is_playoff=1
        GROUP BY t.id
    """, conn)
    if df.empty:
        return df
    df["WIN%"] = (df["W"] / (df["W"] + df["L"]).clip(1)).round(3)
    return df


def _super_bowl_champions(conn):
    return pd.read_sql("""
        SELECT s.year AS Season, t.city||' '||t.name AS Champion, t.abbreviation AS ABV
        FROM seasons s JOIN teams t ON s.champion_team_id=t.id
        ORDER BY s.year DESC
    """, conn)


def _postseason_worst_overall(conn):
    """Worst qualifying postseason player per category (small thresholds)."""
    rows = []

    qb = pd.read_sql("""
        SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT g.id) AS GP,
               SUM(q.completions) AS CMP, SUM(q.attempts) AS ATT, SUM(q.pass_yards) AS YDS,
               SUM(q.pass_tds) AS TD, SUM(q.interceptions) AS INT
        FROM game_qb_stats q JOIN players p ON q.player_id=p.id JOIN teams t ON q.team_id=t.id
        JOIN games g ON q.game_id=g.id AND g.is_playoff=1
        GROUP BY q.player_id HAVING SUM(q.attempts)>=30
    """, conn)
    if not qb.empty:
        qb["RTG"] = qb.apply(lambda r: passer_rating(r.CMP, r.ATT, r.YDS, r.TD, r.INT), axis=1)
        w = qb.sort_values("RTG").iloc[0]
        rows.append(["PASSING", w.Player, w.Team, int(w.GP), "RTG", w.RTG, f"{int(w.ATT)} att"])

    rb = pd.read_sql("""
        SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT g.id) AS GP,
               SUM(r.carries) AS CAR, SUM(r.rush_yards) AS YDS
        FROM game_rb_stats r JOIN players p ON r.player_id=p.id JOIN teams t ON r.team_id=t.id
        JOIN games g ON r.game_id=g.id AND g.is_playoff=1
        GROUP BY r.player_id HAVING SUM(r.carries)>=30
    """, conn)
    if not rb.empty:
        rb["YPC"] = (rb["YDS"] / rb["CAR"].clip(1)).round(2)
        w = rb.sort_values("YPC").iloc[0]
        rows.append(["RUSHING", w.Player, w.Team, int(w.GP), "YPC", w.YPC, f"{int(w.CAR)} car"])

    rec = pd.read_sql("""
        SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT g.id) AS GP,
               SUM(w.targets) AS TGT, SUM(w.receptions) AS REC, SUM(w.rec_yards) AS YDS
        FROM game_wr_stats w JOIN players p ON w.player_id=p.id JOIN teams t ON w.team_id=t.id
        JOIN games g ON w.game_id=g.id AND g.is_playoff=1
        WHERE p.position IN ('WR','TE') GROUP BY w.player_id HAVING SUM(w.targets)>=15
    """, conn)
    if not rec.empty:
        rec["YPR"] = (rec["YDS"] / rec["REC"].clip(1)).round(2)
        w = rec.sort_values("YPR").iloc[0]
        rows.append(["RECEIVING", w.Player, w.Team, int(w.GP), "YPR", w.YPR, f"{int(w.TGT)} tgt"])

    dfn = pd.read_sql("""
        SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT g.id) AS GP, SUM(d.tackles) AS TKL
        FROM game_def_stats d JOIN players p ON d.player_id=p.id JOIN teams t ON d.team_id=t.id
        JOIN games g ON d.game_id=g.id AND g.is_playoff=1
        GROUP BY d.player_id HAVING COUNT(DISTINCT g.id)>=3
    """, conn)
    if not dfn.empty:
        dfn["TKL/G"] = (dfn["TKL"] / dfn["GP"].clip(1)).round(1)
        w = dfn.sort_values("TKL/G").iloc[0]
        rows.append(["DEFENSE", w.Player, w.Team, int(w.GP), "TKL/G", w["TKL/G"], f"{int(w.TKL)} tkl"])

    k = pd.read_sql("""
        SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT g.id) AS GP,
               SUM(k.fg_made) AS FGM, SUM(k.fg_att) AS FGA
        FROM game_k_stats k JOIN players p ON k.player_id=p.id JOIN teams t ON k.team_id=t.id
        JOIN games g ON k.game_id=g.id AND g.is_playoff=1
        GROUP BY k.player_id HAVING SUM(k.fg_att)>=5
    """, conn)
    if not k.empty:
        k["FG%"] = (k["FGM"] / k["FGA"].clip(1) * 100).round(1)
        w = k.sort_values("FG%").iloc[0]
        rows.append(["KICKING", w.Player, w.Team, int(w.GP), "FG%", w["FG%"], f"{int(w.FGA)} fga"])

    p = pd.read_sql("""
        SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT g.id) AS GP,
               SUM(pt.punts) AS PNT, SUM(pt.punt_yards) AS YDS
        FROM game_p_stats pt JOIN players p ON pt.player_id=p.id JOIN teams t ON pt.team_id=t.id
        JOIN games g ON pt.game_id=g.id AND g.is_playoff=1
        GROUP BY pt.player_id HAVING SUM(pt.punts)>=5
    """, conn)
    if not p.empty:
        p["AVG"] = (p["YDS"] / p["PNT"].clip(1)).round(1)
        w = p.sort_values("AVG").iloc[0]
        rows.append(["PUNTING", w.Player, w.Team, int(w.GP), "AVG", w.AVG, f"{int(w.PNT)} pnt"])

    return pd.DataFrame(rows, columns=["Category", "Player", "Team", "GP", "Metric", "Value", "Volume"])


# ── HEADER ────────────────────────────────────────────────────────────────────
st.code("""
╔══════════════════════════════════════╗
║                                      ║
║      G R I D I R O N   S I M        ║
║                                      ║
╚══════════════════════════════════════╝
""", language=None)
st.code(f"  {config.NUM_TEAMS} TEAMS  ·  {config.WEEKS_PER_SEASON}-WEEK SEASON  ·  FOOTBALL SIMULATION ENGINE", language=None)

VIEWS = ["SIMULATE", "STANDINGS", "SCOREBOARD", "STATS", "HISTORY", "PLAYOFFS", "ALL-TIME"]
_cat_picker("active_view", VIEWS)
view = st.session_state["active_view"]
st.code("─" * 62, language=None)

# ── SIMULATE ─────────────────────────────────────────────────────────────────
if view == "SIMULATE":
    current = get_current_season()
    next_yr = (current + 1) if current else config.START_YEAR

    _section("simulation control")
    if current:
        st.info(f"LATEST SEASON: {current}")
    else:
        st.info("NO SEASONS SIMULATED YET.")

    n = st.number_input("SEASONS TO SIMULATE", 1, 1000, 1)
    if st.button(f">> SIMULATE {n} SEASON{'S' if n > 1 else ''}", type="primary"):
        bar = st.progress(0)
        for i in range(n):
            run_season(next_yr + i)
            bar.progress((i + 1) / n)
        st.success(f"DONE — SEASONS {next_yr} THROUGH {next_yr + n - 1}")
        st.rerun()

    _divider()
    _section("danger zone")

    if st.button(">> RESET SIMULATION", type="secondary"):
        st.session_state["confirm_reset"] = True

    if st.session_state.get("confirm_reset"):
        season_count = len(get_seasons())
        st.warning(
            f"WARNING: THIS WILL PERMANENTLY DELETE ALL {season_count} "
            f"SEASON{'S' if season_count != 1 else ''} OF DATA AND GENERATE "
            f"A NEW LEAGUE. THIS CANNOT BE UNDONE."
        )
        col1, col2 = st.columns([1, 5])
        if col1.button("CONFIRM", type="primary"):
            reset_db()
            create_league()
            st.session_state.pop("confirm_reset", None)
            st.rerun()
        if col2.button("CANCEL"):
            st.session_state.pop("confirm_reset", None)
            st.rerun()

# ── STANDINGS ─────────────────────────────────────────────────────────────────
if view == "STANDINGS":
    years = get_seasons()
    if not years:
        st.info("NO DATA — SIMULATE A SEASON FIRST.")
    else:
        yr = st.selectbox("SEASON", years, key="s_yr")
        df = get_standings(yr)

        for conf in ["AFC", "NFC"]:
            _section(conf)
            cdf = df[df["conference"] == conf]
            for div in ["North", "South", "East", "West"]:
                ddf = cdf[cdf["division"] == div].copy()
                if ddf.empty:
                    continue
                st.code(f"  ── {conf.upper()} {div.upper()} ──", language=None)
                out = ddf[["abbreviation", "city", "name", "W", "L", "T", "PCT", "PF", "PA", "DIFF"]].copy()
                out.columns = ["ABV", "CITY", "TEAM", "W", "L", "T", "PCT", "PF", "PA", "DIFF"]
                st.code(tabulate(out, headers="keys", tablefmt="outline", showindex=False), language=None)

# ── SCOREBOARD ────────────────────────────────────────────────────────────────
if view == "SCOREBOARD":
    years = get_seasons()
    if not years:
        st.info("NO DATA — SIMULATE A SEASON FIRST.")
    elif st.session_state.get("selected_game"):
        render_game_detail(st.session_state["selected_game"])
    else:
        search = st.text_input(
            "SEARCH TEAM", key="sc_search",
            placeholder="team name, city, or abbreviation — e.g. iron, hawks, IFT",
        )

        if search and search.strip():
            # ── Team search mode ──
            conn = get_conn()
            like = f"%{search.strip().lower()}%"
            matches = pd.read_sql("""
                SELECT id, abbreviation AS abv, city||' '||name AS full
                FROM teams
                WHERE lower(city) LIKE ? OR lower(name) LIKE ?
                   OR lower(abbreviation) LIKE ? OR lower(city||' '||name) LIKE ?
                ORDER BY full
            """, conn, params=(like, like, like, like))

            if matches.empty:
                st.info(f"NO TEAMS MATCH '{search.strip()}'.")
            else:
                if len(matches) == 1:
                    team_id = int(matches.iloc[0]["id"])
                else:
                    st.code(f"  {len(matches)} TEAMS MATCH — PICK ONE", language=None)
                    opt = st.selectbox("MATCHING TEAMS", matches["full"].tolist(), key="sc_match")
                    team_id = int(matches[matches["full"] == opt].iloc[0]["id"])
                render_team_games(conn, team_id)
            conn.close()

        else:
            # ── Normal week browser ──
            c1, c2 = st.columns(2)
            yr = c1.selectbox("SEASON", years, key="sc_yr")
            week = c2.number_input("WEEK", 1, config.WEEKS_PER_SEASON, 1, key="sc_week")

            _section(f"WEEK {week} — SEASON {yr}")

            conn = get_conn()
            games = pd.read_sql("""
                SELECT g.id AS gid, g.home_score, g.away_score,
                       ht.city||' '||ht.name AS home, ht.abbreviation AS ha,
                       at_.city||' '||at_.name AS away, at_.abbreviation AS aa
                FROM games g
                JOIN seasons s ON g.season_id=s.id
                JOIN teams ht ON g.home_team_id=ht.id
                JOIN teams at_ ON g.away_team_id=at_.id
                WHERE s.year=? AND g.week=? AND g.is_playoff=0
            """, conn, params=(yr, week))
            conn.close()

            if games.empty:
                st.info("NO GAMES FOUND.")
            else:
                cols = st.columns(4)
                for i, (_, g) in enumerate(games.iterrows()):
                    with cols[i % 4]:
                        st.code(_game_card(
                            g["aa"], g["away_score"],
                            g["ha"], g["home_score"]
                        ), language=None)
                        if st.button("VIEW GAME", key=f"view_{int(g['gid'])}",
                                     use_container_width=True):
                            st.session_state["selected_game"] = int(g["gid"])
                            st.rerun()

# ── STATS LEADERS ─────────────────────────────────────────────────────────────
if view == "STATS":
    years = get_seasons()
    if not years:
        st.info("NO DATA — SIMULATE A SEASON FIRST.")
    else:
        yr = st.selectbox("SEASON", years, key="st_yr")
        cat = _cat_picker("stats_cat", ["PASSING", "RUSHING", "RECEIVING", "DEFENSE", "KICKING", "PUNTING"])

        _section(f"{cat} LEADERS — {yr}")
        conn = get_conn()

        if cat == "PASSING":
            df = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team,
                       SUM(q.completions) AS CMP, SUM(q.attempts) AS ATT,
                       SUM(q.pass_yards) AS YDS, SUM(q.pass_tds) AS TD,
                       SUM(q.interceptions) AS INT, SUM(q.rush_yards) AS RushYds
                FROM game_qb_stats q
                JOIN players p ON q.player_id=p.id
                JOIN teams t ON q.team_id=t.id
                JOIN games g ON q.game_id=g.id AND g.is_playoff=0
                JOIN seasons s ON g.season_id=s.id
                WHERE s.year=? GROUP BY q.player_id ORDER BY YDS DESC LIMIT 25
            """, conn, params=(yr,))
            df["CMP%"] = (df["CMP"] / df["ATT"].clip(1) * 100).round(1)
            df["RTG"] = df.apply(lambda r: passer_rating(r.CMP, r.ATT, r.YDS, r.TD, r.INT), axis=1)
            df = df[["Player", "Team", "CMP", "ATT", "CMP%", "YDS", "TD", "INT", "RTG", "RushYds"]]

        elif cat == "RUSHING":
            df = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team, p.position AS Pos,
                       SUM(r.carries) AS CAR, SUM(r.rush_yards) AS YDS, SUM(r.rush_tds) AS TD
                FROM game_rb_stats r
                JOIN players p ON r.player_id=p.id
                JOIN teams t ON r.team_id=t.id
                JOIN games g ON r.game_id=g.id AND g.is_playoff=0
                JOIN seasons s ON g.season_id=s.id
                WHERE s.year=? GROUP BY r.player_id ORDER BY YDS DESC LIMIT 25
            """, conn, params=(yr,))
            df["YPC"] = (df["YDS"] / df["CAR"].clip(1)).round(1)
            df = df[["Player", "Team", "Pos", "CAR", "YDS", "YPC", "TD"]]

        elif cat == "RECEIVING":
            wr_df = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team, p.position AS Pos,
                       SUM(w.targets) AS TGT, SUM(w.receptions) AS REC,
                       SUM(w.rec_yards) AS YDS, SUM(w.rec_tds) AS TD
                FROM game_wr_stats w
                JOIN players p ON w.player_id=p.id
                JOIN teams t ON w.team_id=t.id
                JOIN games g ON w.game_id=g.id AND g.is_playoff=0
                JOIN seasons s ON g.season_id=s.id
                WHERE s.year=? GROUP BY w.player_id
            """, conn, params=(yr,))
            rb_df = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team, 'RB' AS Pos,
                       SUM(r.targets) AS TGT, SUM(r.receptions) AS REC,
                       SUM(r.rec_yards) AS YDS, SUM(r.rec_tds) AS TD
                FROM game_rb_stats r
                JOIN players p ON r.player_id=p.id
                JOIN teams t ON r.team_id=t.id
                JOIN games g ON r.game_id=g.id AND g.is_playoff=0
                JOIN seasons s ON g.season_id=s.id
                WHERE s.year=? GROUP BY r.player_id
            """, conn, params=(yr,))
            df = pd.concat([wr_df, rb_df]).sort_values("YDS", ascending=False).head(25)
            df["YPR"] = (df["YDS"] / df["REC"].clip(1)).round(1)
            df = df[["Player", "Team", "Pos", "TGT", "REC", "YDS", "YPR", "TD"]]

        elif cat == "DEFENSE":
            df = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team, p.position AS Pos,
                       SUM(d.tackles) AS TKL, SUM(d.assists) AS AST,
                       ROUND(SUM(d.sacks),1) AS SCK, SUM(d.interceptions) AS INT,
                       SUM(d.pass_deflections) AS PD, SUM(d.forced_fumbles) AS FF,
                       ROUND(SUM(d.tfl),1) AS TFL
                FROM game_def_stats d
                JOIN players p ON d.player_id=p.id
                JOIN teams t ON d.team_id=t.id
                JOIN games g ON d.game_id=g.id AND g.is_playoff=0
                JOIN seasons s ON g.season_id=s.id
                WHERE s.year=? GROUP BY d.player_id ORDER BY TKL DESC LIMIT 25
            """, conn, params=(yr,))

        elif cat == "KICKING":
            df = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team,
                       SUM(k.fg_made) AS FGM, SUM(k.fg_att) AS FGA,
                       MAX(k.fg_long) AS LNG, SUM(k.xp_made) AS XPM, SUM(k.xp_att) AS XPA
                FROM game_k_stats k
                JOIN players p ON k.player_id=p.id
                JOIN teams t ON k.team_id=t.id
                JOIN games g ON k.game_id=g.id AND g.is_playoff=0
                JOIN seasons s ON g.season_id=s.id
                WHERE s.year=? GROUP BY k.player_id ORDER BY FGM DESC LIMIT 25
            """, conn, params=(yr,))
            df["FG%"] = (df["FGM"] / df["FGA"].clip(1) * 100).round(1)
            df = df[["Player", "Team", "FGM", "FGA", "FG%", "LNG", "XPM", "XPA"]]

        else:
            df = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team,
                       SUM(pt.punts) AS PNT, SUM(pt.punt_yards) AS YDS, SUM(pt.inside_20) AS IN20
                FROM game_p_stats pt
                JOIN players p ON pt.player_id=p.id
                JOIN teams t ON pt.team_id=t.id
                JOIN games g ON pt.game_id=g.id AND g.is_playoff=0
                JOIN seasons s ON g.season_id=s.id
                WHERE s.year=? GROUP BY pt.player_id ORDER BY YDS DESC LIMIT 25
            """, conn, params=(yr,))
            df["AVG"] = (df["YDS"] / df["PNT"].clip(1)).round(1)
            df = df[["Player", "Team", "PNT", "YDS", "AVG", "IN20"]]

        conn.close()
        st.code(tabulate(df, headers="keys", tablefmt="outline", showindex=False), language=None)

# ── HISTORY ───────────────────────────────────────────────────────────────────
if view == "HISTORY":
    years = get_seasons()
    if not years:
        st.info("NO DATA — SIMULATE A SEASON FIRST.")
    else:
        _section("season history")
        rows = []
        for yr in years:
            df = get_standings(yr)
            if df.empty:
                continue
            top = df.iloc[0]
            bot = df.iloc[-1]
            rows.append({
                "SEASON": yr,
                "BEST TEAM": f"{top['city']} {top['name']} ({top['W']}-{top['L']}-{top['T']})",
                "WORST TEAM": f"{bot['city']} {bot['name']} ({bot['W']}-{bot['L']}-{bot['T']})",
                "AVG PTS": round(df["PF"].mean() / max(1, (df["W"] + df["L"] + df["T"]).mean()), 1),
            })
        st.code(tabulate(pd.DataFrame(rows), headers="keys", tablefmt="outline", showindex=False), language=None)

# ── PLAYOFFS ──────────────────────────────────────────────────────────────────
if view == "PLAYOFFS":
    years = get_seasons()
    if not years:
        st.info("NO DATA — SIMULATE A SEASON FIRST.")
    else:
        conn = get_conn()
        po_years = [r["year"] for r in conn.execute(
            "SELECT DISTINCT s.year FROM seasons s JOIN games g ON g.season_id=s.id "
            "WHERE g.is_playoff=1 ORDER BY s.year DESC"
        ).fetchall()]

        if not po_years:
            st.info("NO PLAYOFFS YET — SIMULATE A FULL SEASON FIRST.")
            conn.close()
        else:
            yr = st.selectbox("SEASON", po_years, key="po_yr")

            # Champion banner
            champ = conn.execute(
                "SELECT t.city||' '||t.name AS name, t.abbreviation AS abv "
                "FROM seasons s JOIN teams t ON s.champion_team_id=t.id WHERE s.year=?", (yr,)
            ).fetchone()
            if champ:
                line = f"  ★  {yr} CHAMPIONS:  {champ['name']}  ({champ['abv']})  ★"
                bar = "═" * (len(line) + 2)
                st.code(f"╔{bar}╗\n║ {line} ║\n╚{bar}╝", language=None)

            # Bracket, round by round
            pg = pd.read_sql("""
                SELECT g.playoff_round AS rnd, g.home_score, g.away_score,
                       ht.abbreviation AS ha, at_.abbreviation AS aa,
                       ht.conference AS hconf
                FROM games g JOIN seasons s ON g.season_id=s.id
                JOIN teams ht ON g.home_team_id=ht.id JOIN teams at_ ON g.away_team_id=at_.id
                WHERE s.year=? AND g.is_playoff=1
            """, conn, params=(yr,))

            for rnd in PLAYOFF_ROUNDS:
                rg = pg[pg["rnd"] == rnd]
                if rg.empty:
                    continue
                _section(rnd)
                cols = st.columns(max(1, min(4, len(rg))))
                for i, (_, g) in enumerate(rg.iterrows()):
                    with cols[i % len(cols)]:
                        st.code(_game_card(g["aa"], g["away_score"], g["ha"], g["home_score"]),
                                language=None)

            # Postseason stat leaders for this season
            _divider()
            _section(f"postseason leaders — {yr}")
            pcat = _cat_picker("po_cat", ["PASSING", "RUSHING", "RECEIVING", "DEFENSE", "KICKING", "PUNTING"])
            pdf = _postseason_leaders(conn, pcat, year=yr)
            if pdf.empty:
                st.code("  (no recorded stats)", language=None)
            else:
                st.code(tabulate(pdf, headers="keys", tablefmt="outline", showindex=False), language=None)

            conn.close()

# ── ALL-TIME ──────────────────────────────────────────────────────────────────
if view == "ALL-TIME":
    years = get_seasons()
    if not years:
        st.info("NO DATA — SIMULATE SOME SEASONS FIRST.")
    else:
        conn = get_conn()

        _section("all-time team records")
        team_rec = pd.read_sql("""
            SELECT t.city AS City, t.name AS Team, t.abbreviation AS ABV,
                   t.conference AS Conf, t.division AS Div,
                   COUNT(DISTINCT s.id) AS Seasons,
                   SUM(CASE WHEN (g.home_team_id=t.id AND g.home_score>g.away_score)
                                 OR (g.away_team_id=t.id AND g.away_score>g.home_score)
                            THEN 1 ELSE 0 END) AS W,
                   SUM(CASE WHEN (g.home_team_id=t.id AND g.home_score<g.away_score)
                                 OR (g.away_team_id=t.id AND g.away_score<g.home_score)
                            THEN 1 ELSE 0 END) AS L,
                   SUM(CASE WHEN g.home_score=g.away_score THEN 1 ELSE 0 END) AS T,
                   SUM(CASE WHEN g.home_team_id=t.id THEN g.home_score ELSE g.away_score END) AS PF,
                   SUM(CASE WHEN g.home_team_id=t.id THEN g.away_score ELSE g.home_score END) AS PA
            FROM teams t
            JOIN games g ON (g.home_team_id=t.id OR g.away_team_id=t.id)
            JOIN seasons s ON g.season_id=s.id
            WHERE g.is_playoff=0 GROUP BY t.id
        """, conn)
        gp = (team_rec["W"] + team_rec["L"] + team_rec["T"]).clip(lower=1)
        team_rec["WIN%"] = ((team_rec["W"] + team_rec["T"] * 0.5) / gp).round(3)
        team_rec["DIFF"] = team_rec["PF"] - team_rec["PA"]
        team_rec = team_rec.sort_values("WIN%", ascending=False)
        _team_rec_out = team_rec[["ABV", "City", "Team", "Conf", "Seasons", "W", "L", "T", "WIN%", "PF", "PA", "DIFF"]]
        st.code(tabulate(_team_rec_out, headers="keys", tablefmt="outline", showindex=False), language=None)

        _divider()

        season_records = pd.read_sql("""
            SELECT s.year AS Season, t.city||' '||t.name AS Team, t.abbreviation AS ABV,
                   SUM(CASE WHEN (g.home_team_id=t.id AND g.home_score>g.away_score)
                                 OR (g.away_team_id=t.id AND g.away_score>g.home_score)
                            THEN 1 ELSE 0 END) AS W,
                   SUM(CASE WHEN (g.home_team_id=t.id AND g.home_score<g.away_score)
                                 OR (g.away_team_id=t.id AND g.away_score<g.home_score)
                            THEN 1 ELSE 0 END) AS L,
                   SUM(CASE WHEN g.home_score=g.away_score THEN 1 ELSE 0 END) AS T,
                   SUM(CASE WHEN g.home_team_id=t.id THEN g.home_score ELSE g.away_score END) AS PF,
                   SUM(CASE WHEN g.home_team_id=t.id THEN g.away_score ELSE g.home_score END) AS PA
            FROM teams t
            JOIN games g ON (g.home_team_id=t.id OR g.away_team_id=t.id)
            JOIN seasons s ON g.season_id=s.id
            WHERE g.is_playoff=0 GROUP BY s.id, t.id
        """, conn)

        st.code("  click a numbered button to jump to that team's season in the scoreboard", language=None)
        col1, col2 = st.columns(2)
        with col1:
            _section("best season ever")
            best = season_records.sort_values(["W", "PF"], ascending=False).head(10).reset_index(drop=True)
            _ranked_table_with_buttons(
                best[["Season", "Team", "ABV", "W", "L", "T", "PF", "PA"]], "best_season",
                lambda i: _goto_scoreboard_season(best.iloc[i]["Season"]))
        with col2:
            _section("worst season ever")
            worst = season_records.sort_values(["L", "PA"], ascending=False).head(10).reset_index(drop=True)
            _ranked_table_with_buttons(
                worst[["Season", "Team", "ABV", "W", "L", "T", "PF", "PA"]], "worst_season",
                lambda i: _goto_scoreboard_season(worst.iloc[i]["Season"]))

        _divider()
        _section("all-time individual leaders")
        cat = _cat_picker("at_cat", ["PASSING", "RUSHING", "RECEIVING", "DEFENSE", "KICKING", "PUNTING"])

        if cat == "PASSING":
            df = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team,
                       COUNT(DISTINCT s.id) AS Seasons,
                       SUM(q.completions) AS CMP, SUM(q.attempts) AS ATT,
                       SUM(q.pass_yards) AS YDS, SUM(q.pass_tds) AS TD,
                       SUM(q.interceptions) AS INT, SUM(q.rush_yards) AS RushYds
                FROM game_qb_stats q
                JOIN players p ON q.player_id=p.id
                JOIN teams t ON q.team_id=t.id
                JOIN games g ON q.game_id=g.id AND g.is_playoff=0
                JOIN seasons s ON g.season_id=s.id
                GROUP BY q.player_id ORDER BY YDS DESC LIMIT 25
            """, conn)
            df["CMP%"] = (df["CMP"] / df["ATT"].clip(1) * 100).round(1)
            df["RTG"] = df.apply(lambda r: passer_rating(r.CMP, r.ATT, r.YDS, r.TD, r.INT), axis=1)
            df = df[["Player", "Team", "Seasons", "CMP", "ATT", "CMP%", "YDS", "TD", "INT", "RTG"]]

        elif cat == "RUSHING":
            df = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team,
                       COUNT(DISTINCT s.id) AS Seasons,
                       SUM(r.carries) AS CAR, SUM(r.rush_yards) AS YDS, SUM(r.rush_tds) AS TD
                FROM game_rb_stats r
                JOIN players p ON r.player_id=p.id
                JOIN teams t ON r.team_id=t.id
                JOIN games g ON r.game_id=g.id AND g.is_playoff=0
                JOIN seasons s ON g.season_id=s.id
                GROUP BY r.player_id ORDER BY YDS DESC LIMIT 25
            """, conn)
            df["YPC"] = (df["YDS"] / df["CAR"].clip(1)).round(1)
            df = df[["Player", "Team", "Seasons", "CAR", "YDS", "YPC", "TD"]]

        elif cat == "RECEIVING":
            wr_df = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team, p.position AS Pos,
                       COUNT(DISTINCT s.id) AS Seasons,
                       SUM(w.targets) AS TGT, SUM(w.receptions) AS REC,
                       SUM(w.rec_yards) AS YDS, SUM(w.rec_tds) AS TD
                FROM game_wr_stats w
                JOIN players p ON w.player_id=p.id
                JOIN teams t ON w.team_id=t.id
                JOIN games g ON w.game_id=g.id AND g.is_playoff=0
                JOIN seasons s ON g.season_id=s.id
                GROUP BY w.player_id
            """, conn)
            rb_df = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team, 'RB' AS Pos,
                       COUNT(DISTINCT s.id) AS Seasons,
                       SUM(r.targets) AS TGT, SUM(r.receptions) AS REC,
                       SUM(r.rec_yards) AS YDS, SUM(r.rec_tds) AS TD
                FROM game_rb_stats r
                JOIN players p ON r.player_id=p.id
                JOIN teams t ON r.team_id=t.id
                JOIN games g ON r.game_id=g.id AND g.is_playoff=0
                JOIN seasons s ON g.season_id=s.id
                GROUP BY r.player_id
            """, conn)
            df = pd.concat([wr_df, rb_df]).sort_values("YDS", ascending=False).head(25)
            df["YPR"] = (df["YDS"] / df["REC"].clip(1)).round(1)
            df = df[["Player", "Team", "Pos", "Seasons", "TGT", "REC", "YDS", "YPR", "TD"]]

        elif cat == "DEFENSE":
            df = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team, p.position AS Pos,
                       COUNT(DISTINCT s.id) AS Seasons,
                       SUM(d.tackles) AS TKL, SUM(d.assists) AS AST,
                       ROUND(SUM(d.sacks),1) AS SCK, SUM(d.interceptions) AS INT,
                       SUM(d.pass_deflections) AS PD, SUM(d.forced_fumbles) AS FF,
                       ROUND(SUM(d.tfl),1) AS TFL
                FROM game_def_stats d
                JOIN players p ON d.player_id=p.id
                JOIN teams t ON d.team_id=t.id
                JOIN games g ON d.game_id=g.id AND g.is_playoff=0
                JOIN seasons s ON g.season_id=s.id
                GROUP BY d.player_id ORDER BY TKL DESC LIMIT 25
            """, conn)

        elif cat == "KICKING":
            df = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team,
                       COUNT(DISTINCT s.id) AS Seasons,
                       SUM(k.fg_made) AS FGM, SUM(k.fg_att) AS FGA,
                       MAX(k.fg_long) AS LNG, SUM(k.xp_made) AS XPM, SUM(k.xp_att) AS XPA
                FROM game_k_stats k
                JOIN players p ON k.player_id=p.id
                JOIN teams t ON k.team_id=t.id
                JOIN games g ON k.game_id=g.id AND g.is_playoff=0
                JOIN seasons s ON g.season_id=s.id
                GROUP BY k.player_id ORDER BY FGM DESC LIMIT 25
            """, conn)
            df["FG%"] = (df["FGM"] / df["FGA"].clip(1) * 100).round(1)
            df = df[["Player", "Team", "Seasons", "FGM", "FGA", "FG%", "LNG", "XPM", "XPA"]]

        else:
            df = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team,
                       COUNT(DISTINCT s.id) AS Seasons,
                       SUM(pt.punts) AS PNT, SUM(pt.punt_yards) AS YDS, SUM(pt.inside_20) AS IN20
                FROM game_p_stats pt
                JOIN players p ON pt.player_id=p.id
                JOIN teams t ON pt.team_id=t.id
                JOIN games g ON pt.game_id=g.id AND g.is_playoff=0
                JOIN seasons s ON g.season_id=s.id
                GROUP BY pt.player_id ORDER BY YDS DESC LIMIT 25
            """, conn)
            df["AVG"] = (df["YDS"] / df["PNT"].clip(1)).round(1)
            df = df[["Player", "Team", "Seasons", "PNT", "YDS", "AVG", "IN20"]]

        st.code(tabulate(df, headers="keys", tablefmt="outline", showindex=False), language=None)

        # ── ALL-TIME LEADERS BY POSITION ──
        _divider()
        _section("all-time leaders by position")
        pos = _cat_picker("at_pos", ["QB", "RB", "WR", "TE", "DE", "DT", "LB", "CB", "S", "K", "P"])

        if pos == "QB":
            pdf = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
                       SUM(q.completions) AS CMP, SUM(q.attempts) AS ATT, SUM(q.pass_yards) AS YDS,
                       SUM(q.pass_tds) AS TD, SUM(q.interceptions) AS INT
                FROM game_qb_stats q JOIN players p ON q.player_id=p.id JOIN teams t ON q.team_id=t.id
                JOIN games g ON q.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
                WHERE p.position='QB' GROUP BY q.player_id ORDER BY YDS DESC LIMIT 25
            """, conn)
        elif pos == "RB":
            pdf = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
                       SUM(r.carries) AS CAR, SUM(r.rush_yards) AS YDS, SUM(r.rush_tds) AS TD
                FROM game_rb_stats r JOIN players p ON r.player_id=p.id JOIN teams t ON r.team_id=t.id
                JOIN games g ON r.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
                WHERE p.position='RB' GROUP BY r.player_id ORDER BY YDS DESC LIMIT 25
            """, conn)
        elif pos in ("WR", "TE"):
            pdf = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
                       SUM(w.targets) AS TGT, SUM(w.receptions) AS REC, SUM(w.rec_yards) AS YDS,
                       SUM(w.rec_tds) AS TD
                FROM game_wr_stats w JOIN players p ON w.player_id=p.id JOIN teams t ON w.team_id=t.id
                JOIN games g ON w.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
                WHERE p.position=? GROUP BY w.player_id ORDER BY YDS DESC LIMIT 25
            """, conn, params=(pos,))
        elif pos in ("DE", "DT", "LB", "CB", "S"):
            pdf = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
                       SUM(d.tackles) AS TKL, SUM(d.assists) AS AST, ROUND(SUM(d.sacks),1) AS SCK,
                       SUM(d.interceptions) AS INT, SUM(d.forced_fumbles) AS FF
                FROM game_def_stats d JOIN players p ON d.player_id=p.id JOIN teams t ON d.team_id=t.id
                JOIN games g ON d.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
                WHERE p.position=? GROUP BY d.player_id ORDER BY TKL DESC LIMIT 25
            """, conn, params=(pos,))
        elif pos == "K":
            pdf = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
                       SUM(k.fg_made) AS FGM, SUM(k.fg_att) AS FGA, MAX(k.fg_long) AS LNG,
                       SUM(k.xp_made) AS XPM
                FROM game_k_stats k JOIN players p ON k.player_id=p.id JOIN teams t ON k.team_id=t.id
                JOIN games g ON k.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
                WHERE p.position='K' GROUP BY k.player_id ORDER BY FGM DESC LIMIT 25
            """, conn)
        else:  # P
            pdf = pd.read_sql("""
                SELECT p.name AS Player, t.abbreviation AS Team, COUNT(DISTINCT s.id) AS Seasons,
                       SUM(pt.punts) AS PNT, SUM(pt.punt_yards) AS YDS, SUM(pt.inside_20) AS IN20
                FROM game_p_stats pt JOIN players p ON pt.player_id=p.id JOIN teams t ON pt.team_id=t.id
                JOIN games g ON pt.game_id=g.id AND g.is_playoff=0 JOIN seasons s ON g.season_id=s.id
                WHERE p.position='P' GROUP BY pt.player_id ORDER BY YDS DESC LIMIT 25
            """, conn)

        st.code(f"  [ TOP 25 {pos} — ALL TIME ]", language=None)
        if pdf.empty:
            st.code("  (no recorded stats for this position yet)", language=None)
        else:
            st.code(tabulate(pdf, headers="keys", tablefmt="outline", showindex=False), language=None)

        # ── BEST / WORST GAMES EVER ──
        _divider()
        st.code("  click a numbered button to open that game in the scoreboard", language=None)
        games_sql = """
            SELECT g.id AS gid, s.year AS Season, g.week AS Week,
                   at_.abbreviation||' @ '||ht.abbreviation AS Matchup,
                   g.away_score||'-'||g.home_score AS Score,
                   (g.home_score + g.away_score) AS Total,
                   ABS(g.home_score - g.away_score) AS Margin
            FROM games g
            JOIN seasons s ON g.season_id=s.id
            JOIN teams ht ON g.home_team_id=ht.id
            JOIN teams at_ ON g.away_team_id=at_.id
            WHERE g.is_playoff=0
            ORDER BY Total {dir} LIMIT 10
        """
        gcol1, gcol2 = st.columns(2)
        with gcol1:
            _section("best games ever")
            st.code("  (highest combined score)", language=None)
            best_g = pd.read_sql(games_sql.format(dir="DESC"), conn).reset_index(drop=True)
            _ranked_table_with_buttons(best_g.drop(columns="gid"), "best_games",
                                       lambda i: _goto_scoreboard_game(best_g.iloc[i]["gid"]))
        with gcol2:
            _section("worst games ever")
            st.code("  (lowest combined score)", language=None)
            worst_g = pd.read_sql(games_sql.format(dir="ASC"), conn).reset_index(drop=True)
            _ranked_table_with_buttons(worst_g.drop(columns="gid"), "worst_games",
                                       lambda i: _goto_scoreboard_game(worst_g.iloc[i]["gid"]))

        # ── ALL-TIME WORST BY POSITION ──
        _divider()
        _section("all-time worst by position")
        st.code("  (worst efficiency among qualifying careers)", language=None)
        wpos = _cat_picker("at_worst_pos", ["QB", "RB", "WR", "TE", "DE", "DT", "LB", "CB", "S", "K", "P"])
        wdf = _worst_by_position(conn, wpos)
        st.code(f"  [ WORST 25 {wpos} — ALL TIME ]", language=None)
        if wdf.empty:
            st.code("  (not enough data — play more seasons)", language=None)
        else:
            st.code(tabulate(wdf, headers="keys", tablefmt="outline", showindex=False), language=None)

        # ── ALL-TIME WORST — OVERALL ──
        _divider()
        _section("all-time worst — overall")
        st.code("  (worst qualifying player in each category)", language=None)
        wov = _worst_overall(conn)
        if wov.empty:
            st.code("  (not enough data — play more seasons)", language=None)
        else:
            st.code(tabulate(wov, headers="keys", tablefmt="outline", showindex=False), language=None)

        # ════════ POSTSEASON / ALL-TIME ════════
        ptr = _playoff_team_records(conn)
        if not ptr.empty:
            _divider()
            tcol1, tcol2 = st.columns(2)
            with tcol1:
                _section("best team in playoffs")
                st.code("  (titles, then playoff win%)", language=None)
                best_t = ptr.sort_values(["Titles", "WIN%"], ascending=False).head(10)
                st.code(tabulate(best_t[["ABV", "Team", "Titles", "W", "L", "WIN%", "GP"]],
                                 headers="keys", tablefmt="outline", showindex=False), language=None)
            with tcol2:
                _section("worst team in playoffs")
                st.code("  (lowest playoff win%, min 5 games)", language=None)
                worst_t = ptr[ptr["GP"] >= 5].sort_values(["WIN%", "Titles"]).head(10)
                if worst_t.empty:
                    st.code("  (not enough playoff games yet)", language=None)
                else:
                    st.code(tabulate(worst_t[["ABV", "Team", "Titles", "W", "L", "WIN%", "GP"]],
                                     headers="keys", tablefmt="outline", showindex=False), language=None)

            _divider()
            _section("super bowl champions")
            champs = _super_bowl_champions(conn)
            if champs.empty:
                st.code("  (no champions crowned yet)", language=None)
            else:
                st.code(tabulate(champs, headers="keys", tablefmt="outline", showindex=False), language=None)

            _divider()
            _section("all-time postseason leaders")
            pacat = _cat_picker("po_at_cat", ["PASSING", "RUSHING", "RECEIVING", "DEFENSE", "KICKING", "PUNTING"])
            paldf = _postseason_leaders(conn, pacat, year=None)
            if paldf.empty:
                st.code("  (no recorded stats)", language=None)
            else:
                st.code(tabulate(paldf, headers="keys", tablefmt="outline", showindex=False), language=None)

            _divider()
            _section("all-time postseason worst — overall")
            st.code("  (worst qualifying postseason player per category)", language=None)
            powov = _postseason_worst_overall(conn)
            if powov.empty:
                st.code("  (not enough postseason data yet)", language=None)
            else:
                st.code(tabulate(powov, headers="keys", tablefmt="outline", showindex=False), language=None)

        conn.close()
