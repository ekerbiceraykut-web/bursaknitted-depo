@echo off
cd /d "%~dp0"
python -c "import PyQt6" 2>nul || (
    pip install -r requirements.txt
)
pythonw main.py
