@echo off

echo Stopping MARUTHI...

taskkill /FI "WINDOWTITLE eq MARUTHI Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq MARUTHI Frontend*" /T /F >nul 2>&1

echo.
echo MARUTHI servers stopped.
pause