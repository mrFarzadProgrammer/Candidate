@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 راهنمای آپلود به GitHub و دیپلوی
echo ========================================
echo.
echo فرزاد عزیز، این مراحل رو دنبال کن:
echo.
echo 📝 مرحله 1: ساخت Repository
echo ----------------------------------------
echo 1. به https://github.com/new برو
echo 2. نام: election-bot-system
echo 3. Public انتخاب کن  
echo 4. Create repository بزن
echo.
echo 📤 مرحله 2: Push کردن
echo ----------------------------------------
echo بعد از ساخت repository، این دستورات رو بزن:
echo.
echo git remote remove origin
echo git remote add origin https://github.com/Farzad93/election-bot-system.git
echo git push -u origin main
echo git push origin v1.0.0
echo.
echo 🚀 مرحله 3: دیپلوی
echo ----------------------------------------
echo فایل DEPLOY_INSTRUCTIONS.txt رو باز کن
echo.
pause
