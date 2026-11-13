@echo off
REM Double-click once to install the missing packages into my_ai_app\venv.
cd /d "%~dp0"
call "..\venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
echo.
echo ===== Running the tests =====
python -m pytest -v
echo.
echo Done. If you see "passed" above, double-click run_app.bat to start the app.
pause
