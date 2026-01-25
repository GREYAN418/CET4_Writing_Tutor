@echo off
echo Starting CET4 Writing Tutor...
echo.
cd /d "%~dp0"
.venv\Scripts\streamlit run app.py
pause