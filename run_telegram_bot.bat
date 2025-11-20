@echo off
echo ============================================================
echo   TELEGRAM BOT ISHGA TUSHIRISH
echo ============================================================
echo.
echo [1/2] SMC Server tekshirilmoqda...
timeout /t 2 /nobreak >nul

curl http://127.0.0.1:8000/health 2>nul
if %errorlevel% neq 0 (
    echo.
    echo XATO: SMC Server ishlamayapti!
    echo Iltimos, avval SMC serverni ishga tushiring:
    echo   python smc_server.py
    echo.
    pause
    exit /b 1
)

echo.
echo [2/2] Telegram Bot ishga tushirilmoqda...
echo.
echo ============================================================
echo Bot ishlayapti! Telegram'da /start bosing.
echo SMC Server loglarini ko'rish uchun boshqa terminal oching.
echo Bot to'xtatish uchun Ctrl+C bosing.
echo ============================================================
echo.

node index.js

pause
