@echo off
chcp 65001 > nul
title سیستم مدیریت انتخابات - راه‌اندازی محلی

echo.
echo ═══════════════════════════════════════════════════════════
echo   🚀 سیستم مدیریت بات‌های انتخاباتی
echo ═══════════════════════════════════════════════════════════
echo.

cd /d "%~dp0"

echo [1/5] بررسی virtual environment...
if not exist "venv\" (
    echo ❌ virtual environment یافت نشد!
    echo 📦 در حال ساخت virtual environment...
    python -m venv venv
    echo ✅ virtual environment ساخته شد
)

echo.
echo [2/5] فعال‌سازی virtual environment...
call venv\Scripts\activate.bat

echo.
echo [3/5] بررسی دیتابیس...
if not exist "election_bot.db" (
    echo ❌ دیتابیس یافت نشد!
    echo 📦 در حال ساخت دیتابیس...
    python init_db.py
    echo ✅ دیتابیس ساخته شد
) else (
    echo ✅ دیتابیس موجود است
)

echo.
echo [4/5] تست اتصال به دیتابیس...
python test_sqlite.py

echo.
echo ═══════════════════════════════════════════════════════════
echo   ✅ آماده راه‌اندازی!
echo ═══════════════════════════════════════════════════════════
echo.
echo   انتخاب کنید:
echo   [1] اجرای پنل ادمین
echo   [2] اجرای پنل کاندیدا
echo   [3] اجرای بات‌ها
echo   [4] اجرای همه (3 Terminal جدا)
echo   [0] خروج
echo.
set /p choice="شماره را وارد کنید: "

if "%choice%"=="1" goto admin
if "%choice%"=="2" goto candidate
if "%choice%"=="3" goto bot
if "%choice%"=="4" goto all
if "%choice%"=="0" goto end

:admin
echo.
echo 🔧 در حال اجرای پنل ادمین...
echo 🌐 آدرس: http://127.0.0.1:5000/
echo 👤 لاگین: admin / admin123
echo.
python admin_panel/app.py
goto end

:candidate
echo.
echo 🔧 در حال اجرای پنل کاندیدا...
echo 🌐 آدرس: http://127.0.0.1:5001/
echo.
python candidate_panel/app.py
goto end

:bot
echo.
echo 🤖 در حال اجرای بات‌ها...
echo.
python bot_runner.py
goto end

:all
echo.
echo 🔧 در حال اجرای همه سرویس‌ها...
echo.
echo ⚠️ توجه: 3 پنجره Terminal جدید باز می‌شود
echo.
start cmd /k "cd /d %cd% && venv\Scripts\activate.bat && echo [پنل ادمین] http://127.0.0.1:5000/ && python admin_panel/app.py"
timeout /t 2 > nul
start cmd /k "cd /d %cd% && venv\Scripts\activate.bat && echo [پنل کاندیدا] http://127.0.0.1:5001/ && python candidate_panel/app.py"
timeout /t 2 > nul
start cmd /k "cd /d %cd% && venv\Scripts\activate.bat && echo [بات‌ها] && python bot_runner.py"
echo.
echo ✅ همه سرویس‌ها راه‌اندازی شدند!
echo.
pause
goto end

:end
echo.
echo 👋 خداحافظ!
pause
