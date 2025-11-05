@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 آپلود به GitHub
echo ========================================
echo.

REM بررسی تغییرات
echo 📋 بررسی تغییرات...
git status
echo.

REM دریافت پیام کامیت
set /p commit_message="💬 پیام کامیت را وارد کنید: "
echo.

REM اضافه کردن فایل‌ها
echo 📦 در حال اضافه کردن فایل‌ها...
git add .
echo.

REM کامیت
echo 💾 در حال کامیت...
git commit -m "%commit_message%"
echo.

REM پوش
echo 🚀 در حال آپلود به GitHub...
git push origin main
echo.

echo ✅ تمام! کد شما با موفقیت آپلود شد.
echo.
pause
