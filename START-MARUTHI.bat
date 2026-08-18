@echo off
title MARUTHI Launcher

echo ==========================================
echo        MARUTHI AI RETAIL COPILOT
echo ==========================================
echo.

cd /d "%~dp0"

echo Starting MARUTHI Backend...
start "MARUTHI Backend" /D "%~dp0backend" cmd /k "call venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

timeout /t 4 /nobreak >nul

echo Starting MARUTHI Frontend...
start "MARUTHI Frontend" /D "%~dp0frontend" cmd /k "npm run dev -- --host 127.0.0.1"

timeout /t 6 /nobreak >nul

echo Opening MARUTHI...
start "" "http://localhost:3000"

echo.
echo ==========================================
echo MARUTHI STARTED
echo.
echo Frontend: http://localhost:3000
echo Backend : http://127.0.0.1:8000
echo ==========================================
echo.

exit