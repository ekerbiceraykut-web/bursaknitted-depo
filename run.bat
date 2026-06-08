@echo off
cd /d "%~dp0"
python -c "import PyQt6" 2>nul || (
    echo Gerekli paketler yukleniyor...
    pip install -r requirements.txt
)
python main.py
pause
