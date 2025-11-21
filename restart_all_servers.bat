@echo off
echo.
echo ========================================
echo    Portlar tozalanmoqda...
echo ========================================
echo.

echo 5000-portni bo'shatish...
net stop "5000" 2>nul
taskkill /f /im python.exe /fi "windowtitle eq *:5000*" 2>nul
taskkill /f /im cmd.exe /fi "windowtitle eq Strategy Server*" 2>nul

echo 5001-portni bo'shatish...
net stop "5001" 2>nul
taskkill /f /im python.exe /fi "windowtitle eq *:5001*" 2>nul
taskkill /f /im cmd.exe /fi "windowtitle eq AI Server*" 2>nul

echo 8000-portni bo'shatish...
net stop "8000" 2>nul
taskkill /f /im python.exe /fi "windowtitle eq *:8000*" 2>nul
taskkill /f /im cmd.exe /fi "windowtitle eq SMC Server*" 2>nul

echo.

echo ========================================
echo    SMC+AI Trading System qayta ishga tushirilmoqda
echo ========================================
echo.

echo 1/4 - Strategy Server (Port 5000) ishga tushirilmoqda...
start "Strategy Server" cmd /k "cd /d C:\Qwen\trading signal && python strategy_server.py"

echo.
echo 2/4 - AI Server (Port 5001) ishga tushirilmoqda...
start "AI Server" cmd /k "cd /d C:\Qwen\trading signal && python ai_server.py"

echo.
echo 3/4 - SMC Server (Port 8000) ishga tushirilmoqda...
start "SMC Server" cmd /k "cd /d C:\Qwen\trading signal && python -m uvicorn smc_server:app --host 0.0.0.0 --port 8000"

echo.
echo 4/4 - Telegram Bot ishga tushirilmoqda...
start "Telegram Bot" cmd /k "cd /d C:\Qwen\trading signal && node index.js"

echo.
echo Barcha serverlar ishga tushirildi!
echo Har bir server alohida oynada ochiladi.
echo.
echo Agar serverlar ishlamasa, oldin barcha python.jarayonlarni qo'lda yoping.
echo.
pause