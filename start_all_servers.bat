@echo off
echo.
echo ========================================
echo    SMC+AI Trading System ishga tushirilmoqda
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
echo Serverlar:
echo - Strategy Server: http://localhost:5000
echo - AI Server: http://localhost:5001  
echo - SMC Server: http://localhost:8000
echo - Telegram Bot: Sizning botingiz bilan ishlaydi
echo.
echo Dasturlarni to'xtatish uchun har bir oynani alohida yoping.
echo.
pause