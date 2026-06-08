#!/bin/bash
# Ana Mac'te çalışır — diğer bilgisayarların bağlanacağı sunucuyu başlatır
cd "$(dirname "$0")"
echo "Bursa Knitted Depo — API Sunucusu başlatılıyor..."
python3 server.py
