@echo off
rem Double-click this file to preview the website at http://localhost:8000
cd /d "%~dp0"
where py >nul 2>nul && (py -3 serve.py) || (python serve.py)
pause
