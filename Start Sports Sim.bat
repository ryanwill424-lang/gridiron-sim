@echo off
title Gridiron Sim
cd /d "%~dp0"
echo Starting Gridiron Sim... a browser tab will open in a moment.
echo (Keep this window open while you use it. Close it to stop.)
echo.
if not exist ".venv\Scripts\streamlit.exe" (
    echo Setting up environment for the first time...
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
    echo.
)
".venv\Scripts\streamlit.exe" run app.py
echo.
echo Gridiron Sim has stopped. You can close this window.
pause
