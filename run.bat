@echo off
cd /d "%~dp0"

REM Acilista guncellemeyi otomatik cek (git ve .git klasoru varsa)
if exist ".git" (
    git pull origin main >nul 2>nul
)

python -c "import PyQt6" 2>nul || (
    pip install -r requirements.txt
)
start "" pythonw main.py
