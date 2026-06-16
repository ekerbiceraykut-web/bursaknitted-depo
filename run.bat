@echo off
cd /d "%~dp0"

REM Python kurulu mu kontrol et
python --version >nul 2>nul
if errorlevel 1 (
    echo HATA: Python bulunamadi!
    echo.
    echo Lutfen https://www.python.org adresinden Python indirin.
    echo Kurulum sirasinda "Add Python to PATH" secenegini isaretleyin.
    echo.
    pause
    exit /b 1
)

REM Paketleri kontrol et, eksikse yukle
python -c "import PyQt6" 2>nul || (
    echo Gerekli kutuphaneler yukleniyor, lutfen bekleyin...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo HATA: Kutuphaneler yuklenemedi.
        echo CMD acip "pip install -r requirements.txt" komutunu calistirin.
        pause
        exit /b 1
    )
)

REM Onceki hata logunu temizle
if exist "error.log" del "error.log"

REM Guncelleme al
if exist ".git" (
    git pull origin main >nul 2>nul
)

REM Programi baslat
start "" pythonw main.py

REM Kisa bekleme — pythonw hemen cokerse error.log olusur
timeout /t 3 /nobreak >nul

REM Hata logu olustuysa goster
if exist "error.log" (
    echo.
    echo HATA: Program baslaticakti ancak bir hata olustu.
    echo Hata detaylari asagida:
    echo.
    type error.log
    echo.
    pause
)
