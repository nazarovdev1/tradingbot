@echo off
echo.
echo ========================================
echo    SMC Server ishga tushirilmoqda (Port 8000)
echo ========================================
echo.

cd /d C:\Qwen\trading signal
python -m uvicorn smc_server:app --host 0.0.0.0 --port 8000

pause