@echo off
echo Starting SMC+AI Trading System...
echo.

echo Starting Strategy Server (Python)...
start cmd /k "cd /d C:\Qwen\trading signal && python strategy_server.py"

timeout /t 5 /nobreak >nul

echo Starting Telegram Bot (Node.js)...
node index.js

pause