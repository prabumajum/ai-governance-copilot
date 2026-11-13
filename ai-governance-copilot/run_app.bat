@echo off
REM Double-click to start the app. Uses the venv in the parent folder (my_ai_app\venv).
cd /d "%~dp0"
call "..\venv\Scripts\activate.bat"
python -m streamlit run app.py
pause
