# Handoff — Gridiron Sim — 2026-06-28

GOAL: A fictional-football season simulator (Streamlit + SQLite, terminal/ASCII
style). Currently feature-complete through the postseason; in a "built, awaiting
real-world testing" state.

DONE (recent sessions):
- Full postseason: 14-team bracket → Super Bowl, champions tracked, postseason stats.
- ALL-TIME tab: team records, best/worst season, best/worst games, leaders by
  position, worst-player tables, postseason all-time views.
- Best/Worst season & games leaderboards rendered as terminal ASCII tables with
  numbered buttons that jump to the game/season in the Scoreboard view.
- Session-state view nav (replaced st.tabs so cross-view navigation works).
- Scoreboard team search (by city/name/abbrev) → that team's season games.
- Game detail view: ASCII player-figure animation + commentary + rare events.
- Player career caps (max 25 seasons, variable) + aging/retirement.
- Added projects/sports-sim/CLAUDE.md (project memory) with the gotchas list.

NEXT STEP: User to fully restart the app (close the terminal, relaunch
"Start Sports Sim.bat" — not just a browser refresh) and click through the new
PLAYOFFS view + ALL-TIME numbered-button navigation + team search to confirm they
render and navigate correctly on a fresh process.

KEY DECISIONS:
- Tables use tabulate-in-st.code, not st.dataframe (theme can't reach the iframe).
- Navigation is session-state driven, not st.tabs (tabs can't be switched in code).
- reset_db drops tables instead of deleting the file (Windows WAL lock).
- Career length capped via per-player career_cap (skewed, max 25), not just age.

OPEN QUESTIONS / BLOCKERS:
- History tab calls get_standings() per season in a loop — could be slow after many
  seasons. Known inefficiency, no complaint yet. Optimize only if it actually drags.
- Phase 4 "visual simulation" was scoped but never started — decide if it's wanted.

WHERE THINGS ARE: app.py (all UI), engine/ (sim logic), data/database.py (schema +
migrations). Run via "Start Sports Sim.bat". See CLAUDE.md for layout + gotchas +
the temp-DB testing approach.

SUGGESTED NEXT SKILLS/COMMANDS:
- Read CLAUDE.md first (gotchas), especially the "restart the process" trap.
- If touching engine/data code, verify against an isolated temp DB, never league.db.
