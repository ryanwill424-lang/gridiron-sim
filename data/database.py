import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "league.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def reset_db():
    """Wipe all data without deleting the database file. Deleting the file
    fails on Windows because SQLite (WAL mode) keeps it locked while open, so
    we drop every table inside a connection instead, then rebuild the schema."""
    conn = get_conn()
    try:
        # Flush the WAL so nothing is left dangling, then drop every table.
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except Exception:
            pass
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()]
        for t in tables:
            conn.execute(f"DROP TABLE IF EXISTS {t}")
        # Reset AUTOINCREMENT counters so IDs start fresh again.
        try:
            conn.execute("DELETE FROM sqlite_sequence")
        except Exception:
            pass  # sqlite_sequence only exists once an AUTOINCREMENT table has been used
        conn.commit()
    finally:
        conn.close()
    init_db()


def init_db():
    conn = get_conn()
    conn.executescript("""
    PRAGMA journal_mode=WAL;

    CREATE TABLE IF NOT EXISTS seasons (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER UNIQUE
    );

    CREATE TABLE IF NOT EXISTS teams (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        city         TEXT, name TEXT, abbreviation TEXT,
        conference   TEXT, division TEXT,
        off_rating   REAL, def_rating REAL
    );

    CREATE TABLE IF NOT EXISTS players (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        team_id  INTEGER, name TEXT, position TEXT,
        overall  REAL,    age  INTEGER,
        FOREIGN KEY (team_id) REFERENCES teams(id)
    );

    CREATE TABLE IF NOT EXISTS games (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        season_id    INTEGER, week INTEGER,
        home_team_id INTEGER, away_team_id INTEGER,
        home_score   INTEGER, away_score   INTEGER,
        is_playoff   INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS game_team_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER, team_id INTEGER,
        pass_yards INTEGER, rush_yards INTEGER, total_yards INTEGER,
        first_downs INTEGER, third_down_conv INTEGER, third_down_att INTEGER,
        red_zone_conv INTEGER, red_zone_att INTEGER,
        turnovers INTEGER, sacks_allowed INTEGER,
        penalties INTEGER, penalty_yards INTEGER,
        top_seconds INTEGER, pass_tds INTEGER, rush_tds INTEGER
    );

    CREATE TABLE IF NOT EXISTS game_qb_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER, player_id INTEGER, team_id INTEGER,
        completions INTEGER, attempts INTEGER, pass_yards INTEGER,
        pass_tds INTEGER, interceptions INTEGER,
        rush_attempts INTEGER, rush_yards INTEGER
    );

    CREATE TABLE IF NOT EXISTS game_rb_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER, player_id INTEGER, team_id INTEGER,
        carries INTEGER, rush_yards INTEGER, rush_tds INTEGER,
        targets INTEGER, receptions INTEGER, rec_yards INTEGER, rec_tds INTEGER
    );

    CREATE TABLE IF NOT EXISTS game_wr_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER, player_id INTEGER, team_id INTEGER,
        targets INTEGER, receptions INTEGER, rec_yards INTEGER, rec_tds INTEGER
    );

    CREATE TABLE IF NOT EXISTS game_def_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER, player_id INTEGER, team_id INTEGER,
        tackles INTEGER, assists INTEGER, sacks REAL,
        interceptions INTEGER, forced_fumbles INTEGER,
        fumble_recoveries INTEGER, pass_deflections INTEGER, tfl REAL
    );

    CREATE TABLE IF NOT EXISTS game_k_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER, player_id INTEGER, team_id INTEGER,
        fg_made INTEGER, fg_att INTEGER, fg_long INTEGER,
        xp_made INTEGER, xp_att INTEGER
    );

    CREATE TABLE IF NOT EXISTS game_p_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER, player_id INTEGER, team_id INTEGER,
        punts INTEGER, punt_yards INTEGER, inside_20 INTEGER
    );
    """)
    conn.commit()

    # Safe migration: add retired column if it doesn't exist yet
    try:
        conn.execute("ALTER TABLE players ADD COLUMN retired INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass  # column already exists

    # Safe migration: career-length tracking columns
    try:
        conn.execute("ALTER TABLE players ADD COLUMN seasons_played INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE players ADD COLUMN career_cap INTEGER")
        conn.commit()
    except Exception:
        pass

    # Safe migration: postseason columns
    try:
        conn.execute("ALTER TABLE games ADD COLUMN playoff_round TEXT")
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE seasons ADD COLUMN champion_team_id INTEGER")
        conn.commit()
    except Exception:
        pass

    # Backfill any players missing a career_cap (e.g. created before this
    # migration). Skew toward shorter careers, hard ceiling 25; estimate
    # seasons already played from age so veterans are correctly advanced.
    import numpy as np
    rows = conn.execute("SELECT id, age FROM players WHERE career_cap IS NULL").fetchall()
    for r in rows:
        cap = int(np.clip(round(np.random.normal(8, 5)), 1, 25))
        played = max(0, (r["age"] if r["age"] is not None else 22) - 22)
        played = min(played, cap)  # never exceed the cap
        conn.execute("UPDATE players SET career_cap=?, seasons_played=? WHERE id=?",
                     (cap, played, r["id"]))
    if rows:
        conn.commit()

    conn.close()
