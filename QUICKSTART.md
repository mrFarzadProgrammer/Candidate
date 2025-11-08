# 🚀 راهنمای سریع - راه‌اندازی روی سرور

## 📦 ساختار پروژه (تمیز شده)

```
candidate/
├── admin_panel/          # پنل مدیریت ادمین
├── candidate_panel/      # پنل کاندیداها
├── bot_engine/          # موتور بات تلگرام
├── config/              # تنظیمات
├── database/            # مدل‌های دیتابیس
├── static/              # فایل‌های CSS/JS
├── templates/           # قالب‌های HTML
├── uploads/             # آپلود فایل‌ها
├── bot_runner.py        # اجرای بات‌ها
├── init_db.py           # ساخت دیتابیس
├── requirements.txt     # کتابخانه‌ها
├── START.bat            # راه‌اندازی محلی
└── README.md
```

---

## ⚡ راه‌اندازی سریع روی PythonAnywhere

### 1️⃣ Pull آخرین تغییرات

```bash
cd ~/Candidate
git pull origin main
```

### 2️⃣ فعال‌سازی محیط و ساخت دیتابیس

```bash
source ~/.virtualenvs/myenv/bin/activate
rm -f election_bot.db
python init_db.py
```

### 3️⃣ تنظیم WSGI

برو به: **Web → WSGI configuration file**

```python
import sys
import os

project_home = '/home/farzad93/Candidate'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

venv_path = '/home/farzad93/.virtualenvs/myenv'
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

os.environ['DATABASE_URL'] = f'sqlite:///{project_home}/election_bot.db'
os.environ['ADMIN_SECRET_KEY'] = '3b72055e598775190cbeabd66a6c8b1222bc2422f6a2fa3a5e5b9b28b6ff0ac9'
os.environ['CANDIDATE_SECRET_KEY'] = 'f33f8dd3ca0fe35c21fac3dfbfb2e001fe98c6f4e9986ec3beec4c700605ce34'

from admin_panel.app import app as admin_app
application = admin_app
```

### 4️⃣ Reload

کلیک: **Reload farzad93.pythonanywhere.com**

---

## 🧪 تست سیستم

### پنل ادمین
- آدرس: https://farzad93.pythonanywhere.com/
- لاگین: `admin` / `admin123`

### ساخت بات
1. از @BotFather توکن بگیر
2. در پنل ادمین: کاندیداها → راه‌اندازی بات
3. توکن رو وارد کن

### اجرای بات
```bash
cd ~/Candidate
source ~/.virtualenvs/myenv/bin/activate
python bot_runner.py
```

---

## 🔍 دیباگ و خطایابی

### چک لاگ‌ها
```bash
# Error log پنل‌ها
tail -f /var/log/farzad93.pythonanywhere.com.error.log

# بات‌ها (در console که bot_runner.py اجرا شده)
# خروجی مستقیم می‌بینی
```

### تست دیتابیس
```bash
cd ~/Candidate
source ~/.virtualenvs/myenv/bin/activate
python
```

```python
from database.models import db, Admin, Candidate, BotInstance
from admin_panel.app import app

with app.app_context():
    print(f"Admins: {Admin.query.count()}")
    print(f"Candidates: {Candidate.query.count()}")
    print(f"Bots: {BotInstance.query.count()}")
```

---

## 🐛 مشکلات رایج

### ❌ 502 Bad Gateway
**حل:** Reload کن Web App

### ❌ Internal Server Error
**حل:** چک کن error.log

### ❌ بات جواب نمیده
**حل:** 
1. چک کن bot_runner.py در حال اجرا است
2. چک کن توکن صحیح است
3. چک کن بات در دیتابیس active است

---

## 📝 نکات مهم

- ✅ دیتابیس: SQLite محلی (election_bot.db)
- ✅ پنل‌ها: PythonAnywhere
- ✅ بات‌ها: PythonAnywhere Console
- ✅ روت پروژه: تمیز و مرتب

---

## 🎯 مراحل بعدی

1. **توسعه بات:** کد بات رو کامل کن
2. **تست کامل:** روی سرور تست کن
3. **دیپلوی نهایی:** روی VPS خودت

---

**آماده برای توسعه! 🚀**
