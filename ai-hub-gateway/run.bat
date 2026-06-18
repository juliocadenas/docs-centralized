@echo off
echo ============================================
echo   AI Hub Madrid - Gateway API
echo   http://localhost:9000
echo ============================================
echo.
cd /d "%~dp0"
set PYTHONPATH=%~dp0
python main.py
pause