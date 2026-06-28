# Gridiron Sim — Project Memory

A fictional-football simulation: a Streamlit web app over a SQLite database that
simulates seasons (regular season + playoffs + Super Bowl), tracks every standard
football stat, and presents it in a terminal/ASCII style.

## How to run

- Windows: double-click **`Start Sports Sim.bat`** (creates `.venv`, installs
  `requirements.txt`, runs `streamlit run app.py`).
- Manual: `.venv\Scripts\streamlit run app.py`
- Python deps: streamlit, pandas, numpy, tabulate.

## Layout

| Path | Role |
|---|---|
| `app.py` | All UI (Streamlit). Views, helpers, game-detail, ASCII animation |
| `config.py` | `NUM_TEAMS=32`, `WEEKS_PER_SEASON=17`, `START_YEAR=2025` |
| `data/database.py` | SQLite: `get_conn`, `init_db` (schema + safe migrations), `reset_db` |
| `engine/names.py` | Fictional cities, team names, abbreviations, player names |
| `engine/player.py` | `ROSTER_SLOTS`, `generate_roster`, `random_career_cap` (max 25 seasons) |
| `engine/game.py` | `simulate_game`, `_gen_team_stats`, `_gen_player_stats` |
| `engine/league.py` | `league_exists`, `create_league` |
| `engine/season.py` | `run_season`, `_save_game`, playoff sim, `_age_and_retire` |

DB tables: `seasons`, `teams`, `players`, `games`, and per-category stat tables
(`game_team_stats`, `game_qb_stats`, `game_rb_stats`, `game_wr_stats`,
`game_def_stats`, `game_k_stats`, `game_p_stats`).

## Conventions

- **Terminal/ASCII aesthetic.** Tables render with `tabulate(..., tablefmt="outline")`
  inside `st.code(...)`, NOT `st.dataframe` (see gotchas). Green-on-black via injected CSS.
- Navigation is a session-state view selector (`st.session_state["active_view"]`),
  rendered with `_cat_picker`. We do NOT use `st.tabs` (can't switch programmatically).
- Reusable UI helpers: `_section`, `_divider`, `_game_card`, `_cat_picker`,
  `_ranked_table_with_buttons`, `render_game_detail`, `render_team_games`.
- Schema changes go through the safe `try/except ALTER TABLE` pattern in `init_db`
  (SQLite has no `ADD COLUMN IF NOT EXISTS`).
- New per-game data is saved through `_save_game` (used by both regular season and playoffs).

## Gotchas (grow this list — add a line whenever I get something wrong)

- **Restart the process after editing engine/data code.** Streamlit caches imported
  modules; a browser refresh runs old code. Fully close the terminal and relaunch the
  `.bat`. If it still acts stale, delete `__pycache__/` in the project, `data/`, `engine/`.
- **`reset_db` must NOT delete the DB file.** SQLite WAL keeps it locked on Windows →
  `PermissionError [WinError 32]`. Drop the tables inside a connection instead.
- **pandas `.T` footgun.** Inside `df.apply(lambda r: ... r.T ...)`, `r.T` is the row
  *transpose*, not the column named "T". Use vectorized column ops for W/L/T math.
- **Regular-season stat queries must filter `is_playoff=0`;** playoff views use
  `is_playoff=1`. The shared trick is on the JOIN: `JOIN games g ON x.game_id=g.id AND g.is_playoff=0`.
- **`st.dataframe` renders in an iframe the theme CSS can't reach** → it looks un-styled.
  Use `tabulate` in `st.code` for the terminal look; add interactivity with numbered buttons.
- **Unicode/box-drawing chars:** the app is UTF-8. When testing via a console, force UTF-8
  stdout — don't let Windows cp1252 decode it.

## Testing approach

- Verify against an **isolated temp database** — override `data.database.DB_PATH` to a temp
  file in the test. NEVER run tests against the real `league.db`.
- To exercise `app.py` headlessly, stub the `streamlit` module (no-op functions + a fake
  `session_state` dict) before importing it, then call the helper functions directly.
- Pure custom code (e.g. the zip writer in the converter projects) can be validated
  cross-tool: build with Node/Python, verify with the other.
