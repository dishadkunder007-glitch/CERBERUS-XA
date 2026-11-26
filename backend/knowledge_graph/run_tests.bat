@echo off
cd /d "%~dp0"
echo Running Contradiction Detection Automated Test Suite...
.\.venv\Scripts\python.exe -m pytest tests\ -v --tb=short
pause
