# 📝 راهنمای آپلود به GitHub و دیپلوی

## 1️⃣ ایجاد مخزن در GitHub

1. به [github.com](https://github.com) برید و وارد شوید
2. روی دکمه **"New"** یا **"+"** کلیک کنید
3. اطلاعات را وارد کنید:
   - **Repository name:** `election-bot-system`
   - **Description:** `🗳️ سیستم جامع مدیریت بات‌های انتخاباتی تلگرام - Telegram Election Bot Management System`
   - **Visibility:** Public یا Private (انتخاب کنید)
   - ✅ **Initialize without README** (چون ما قبلاً README داریم)
4. روی **Create repository** کلیک کنید

## 2️⃣ پوش کردن کد به GitHub

بعد از ایجاد مخزن، این دستورات رو در ترمینال اجرا کنید:

```powershell
cd C:\Workspace\candidate

# اگر قبلاً remote اضافه کردید، اول حذفش کنید:
git remote remove origin

# اضافه کردن remote جدید (آدرس مخزن خودتون رو جایگزین کنید):
git remote add origin https://github.com/YOUR_USERNAME/election-bot-system.git

# Push کردن
git push -u origin main
```

اگر از احراز هویت دو مرحله‌ای استفاده می‌کنید، نیاز به Personal Access Token دارید:
1. Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token → Select scopes: `repo`
3. از این token به جای password استفاده کنید

## 3️⃣ دیپلوی در Render.com (رایگان)

### مرحله 1: ساخت حساب
1. به [render.com](https://render.com) برید
2. Sign Up → با GitHub وارد شوید
3. به Render اجازه دسترسی به مخزن خود را بدهید

### مرحله 2: ایجاد PostgreSQL Database
1. Dashboard → New → PostgreSQL
2. تنظیمات:
   - **Name:** `election-bot-db`
   - **Database:** `election_bot`
   - **User:** `election_user`
   - **Region:** انتخاب کنید (Frankfurt برای ایران بهتره)
   - **Plan:** Free
3. Create Database
4. **Internal Database URL** را کپی کنید و ذخیره کنید

### مرحله 3: ایجاد Web Service
1. Dashboard → New → Web Service
2. Connect repository → مخزن خود را انتخاب کنید
3. تنظیمات:
   - **Name:** `election-bot-system`
   - **Region:** همان region دیتابیس
   - **Branch:** main
   - **Root Directory:** (خالی بگذارید)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Plan:** Free

### مرحله 4: تنظیم Environment Variables
در بخش Environment Variables این متغیرها را اضافه کنید:

```
DATABASE_URI = <internal-database-url-from-step-2>
ADMIN_SECRET_KEY = <generate-random-32-char-string>
CANDIDATE_SECRET_KEY = <generate-random-32-char-string>
```

برای تولید کلید تصادفی:
```python
import secrets
print(secrets.token_hex(32))
```

### مرحله 5: Deploy
1. Create Web Service
2. منتظر بمانید تا build تکمیل شود (3-5 دقیقه)
3. لینک اپلیکیشن شما: `https://election-bot-system.onrender.com`

### مرحله 6: مقداردهی اولیه دیتابیس
1. در صفحه Web Service → Shell (بالای صفحه)
2. دستور زیر را اجرا کنید:
```bash
python init_db.py
```
3. باید پیام "✅ مقداردهی اولیه با موفقیت انجام شد!" را ببینید

## 4️⃣ تست سیستم

### دسترسی به پنل‌ها:
- **صفحه اصلی:** `https://your-app.onrender.com/`
- **پنل ادمین:** `https://your-app.onrender.com/admin/`
  - نام کاربری: `admin`
  - رمز عبور: `admin123`
- **پنل نماینده:** `https://your-app.onrender.com/candidate/`

### راه‌اندازی اولین بات:
1. وارد پنل ادمین شوید
2. یک نماینده ایجاد کنید
3. از BotFather یک بات بسازید:
   - به `@BotFather` در تلگرام پیام دهید
   - `/newbot` را بزنید
   - نام و username بات را وارد کنید
   - توکن را کپی کنید
4. در پنل ادمین → نمایندگان → راه‌اندازی بات
5. توکن و username بات را وارد کنید
6. بات شما آماده است! 🎉

## 5️⃣ نکات مهم

### ⚠️ محدودیت‌های Free Plan:
- سرویس بعد از 15 دقیقه عدم استفاده خاموش می‌شود
- اولین درخواست بعد از خاموش شدن 30-60 ثانیه طول می‌کشد
- 750 ساعت رایگان در ماه

### 🔧 برای جلوگیری از خاموش شدن:
1. از UptimeRobot.com استفاده کنید (رایگان)
2. هر 14 دقیقه یک ping به اپ بزنید

### 🔒 امنیت:
1. **حتماً رمز عبور admin را تغییر دهید**
2. SECRET_KEY های قوی استفاده کنید
3. توکن بات را محرمانه نگه دارید

## 6️⃣ آپدیت کردن پروژه

هر وقت کد را تغییر دادید:

```powershell
cd C:\Workspace\candidate

git add .
git commit -m "توضیح تغییرات"
git push origin main
```

Render به صورت خودکار اپلیکیشن را دوباره deploy می‌کند.

## 🆘 عیب‌یابی

### خطای "Application failed to respond"
- در Logs بررسی کنید
- مطمئن شوید DATABASE_URI صحیح است
- `python init_db.py` را دوباره اجرا کنید

### بات کار نمی‌کند
- در Logs دنبال خطا بگردید
- مطمئن شوید توکن بات صحیح است
- در تلگرام `/start` را بزنید

### دیتابیس متصل نمی‌شود
- Internal Database URL را چک کنید
- مطمئن شوید PostgreSQL در همان region است

---

## 📞 نیاز به کمک؟

اگر در هر مرحله مشکلی داشتید:
1. Logs را در Render بررسی کنید
2. به مستندات پروژه مراجعه کنید
3. در GitHub issue باز کنید

**موفق باشید! 🚀**
