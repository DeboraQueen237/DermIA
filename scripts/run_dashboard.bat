@echo off
echo ==========================================
echo   Lancement du Tableau de Bord DermIA
echo ==========================================
cd /d "%~dp0\.."
call .venv-ml\Scripts\activate.bat
streamlit run dashboard/app.py --server.port 8501
pause
