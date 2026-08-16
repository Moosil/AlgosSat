@echo off
uv lock --upgrade
uv sync
cd /d "%~dp0"
call .venv/scripts/activate
marimo edit --watch
pause