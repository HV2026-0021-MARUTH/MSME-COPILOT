@echo off
title MARUTHI Setup
echo ==========================================
echo    MARUTHI REPOSITORY SETUP (WINDOWS)
echo ==========================================
echo.

cd /d "%~dp0"

echo [1/5] Setting up environment variables...
if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env" >nul
    echo   Created backend\.env
) else (
    echo   backend\.env already exists.
)

if not exist "frontend\.env" (
    copy "frontend\.env.example" "frontend\.env" >nul
    echo   Created frontend\.env
) else (
    echo   frontend\.env already exists.
)

echo.
echo [2/5] Setting up Python backend environment...
cd backend
if not exist "venv" (
    python -m venv venv
    echo   Created virtual environment.
)
call venv\Scripts\activate.bat
echo   Installing backend dependencies (this may take a minute)...
pip install -r ..\requirements.txt >nul
cd ..

echo.
echo [3/5] Setting up Node frontend environment...
cd frontend
if not exist "node_modules" (
    echo   Installing frontend dependencies (this may take a minute)...
    call npm install >nul
) else (
    echo   node_modules already exists.
)
cd ..

echo.
echo [4/5] Initializing Database and injecting Dummy Data...
cd backend
python -c "from app.db.database import init_sqlite_db_and_seed; init_sqlite_db_and_seed()"
cd ..

echo.
echo [5/5] Running Backend Tests...
call backend\venv\Scripts\activate.bat
pytest

echo.
echo ==========================================
echo SETUP COMPLETE!
echo You can now run the app by double-clicking START-MARUTHI.bat
echo ==========================================
pause
