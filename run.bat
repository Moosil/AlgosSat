@echo off
cd /d "%~dp0"
call .venv/scripts/activate
marimo edit
pause