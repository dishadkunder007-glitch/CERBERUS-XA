@echo off
cd /d "%~dp0"
echo Starting Contradiction Detection Streamlit Dashboard...
.\.venv\Scripts\python.exe -m streamlit run app.py
pause
