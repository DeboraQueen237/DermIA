@echo off
echo ==========================================
echo    Lancement de l'API Backend DermIA
echo ==========================================
cd /d "%~dp0\.."
call .venv-ml\Scripts\activate.bat
python backend/run_server.py
pause
