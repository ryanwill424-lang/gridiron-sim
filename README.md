# Gridiron Sim

A fictional-football season simulator — a Streamlit web app over SQLite that
simulates entire seasons (regular season → playoffs → Super Bowl), tracks every
standard football stat, and presents it all in a terminal/ASCII style. No real
teams or players: 32 fictional teams across two conferences and four divisions each.

## Features

- **Simulate** any number of seasons at once.
- **Standings** by conference/division, full **Scoreboard** with team search.
- **Game detail view** with an ASCII player-figure animation + commentary + rare events.
- **Stats leaders** for every position group (passing, rushing, receiving, defense,
  kicking, punting).
- **Playoffs** — a 14-team bracket through to a Super Bowl, with champions tracked.
- **All-Time** records: team records, best/worst seasons & games, leaders and worst
  performers by position, and postseason all-time views.
- **Player careers** — aging, retirement, and a per-player career cap (max 25 seasons).

## Run it

```sh
# Windows
"Start Sports Sim.bat"          # creates a venv, installs deps, launches the app

# or manually (any OS)
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # (Scripts\ on Windows; bin/ elsewhere)
.venv/Scripts/streamlit run app.py
```

The SQLite database (`data/league.db`) is created automatically on first run.

## Layout

| Path | Role |
|---|---|
| `app.py` | Streamlit UI — views, game detail, ASCII animation |
| `config.py` | Tunables (number of teams, weeks per season, start year) |
| `data/database.py` | SQLite schema, migrations, connection helpers |
| `engine/` | Simulation: team/player generation, game sim, seasons, playoffs |

## Tech

Python · Streamlit · SQLite · pandas · numpy
