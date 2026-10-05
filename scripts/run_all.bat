@echo off
echo ========================================================
echo        DermIA - Demarrage Global des Services
echo ========================================================
cd /d "%~dp0\.."

start "DermIA Backend API (Port 8000)" cmd /k "scripts\run_backend.bat"
timeout /t 3 /nobreak >nul
start "DermIA Dashboard Streamlit (Port 8501)" cmd /k "scripts\run_dashboard.bat"

echo.
echo [OK] Backend API : http://127.0.0.1:8000/docs
echo [OK] Dashboard   : http://127.0.0.1:8501
echo.
pause
