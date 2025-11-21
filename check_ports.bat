@echo off
echo.
echo ========================================
echo    Band qilingan portlarni tekshirish
echo ========================================
echo.

echo 5000 port uchun jarayon:
netstat -ano | findstr :5000
echo.

echo 5001 port uchun jarayon:
netstat -ano | findstr :5001
echo.

echo 8000 port uchun jarayon:
netstat -ano | findstr :8000
echo.

echo Barcha band qilingan jarayonlarni ko'rish:
netstat -an

echo.
pause