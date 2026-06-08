#!/bin/bash
cd "$(dirname "$0")"
if ! python3 -c "import PyQt6" 2>/dev/null; then
    echo "Gerekli paketler yükleniyor..."
    pip3 install -r requirements.txt
fi
python3 main.py
