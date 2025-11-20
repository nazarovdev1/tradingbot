@echo off
echo ===================================================
echo   SMC + AI TRADING BOT STARTUP SCRIPT
echo ===================================================

echo [1/2] Starting SMC + AI Analysis Server...
start "SMC Server" cmd /k "python smc_server.py"

echo Waiting 10 seconds for server to initialize...
timeout /t 10 /nobreak >nul

echo [2/2] Starting Telegram Bot...
echo Bot is running! Check the 'SMC Server' window for analysis logs.
echo Press Ctrl+C to stop the bot.
node index.js

pause
