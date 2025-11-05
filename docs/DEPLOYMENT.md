# 🚀 راهنمای دیپلوی

<div dir="rtl">

## گزینه‌های دیپلوی رایگان

### 1️⃣ Render.com (توصیه می‌شود)

**مزایا:**
- ✅ رایگان و بدون نیاز به کارت اعتباری
- ✅ پشتیبانی از PostgreSQL
- ✅ Auto-deploy از GitHub
- ✅ SSL رایگان

**مراحل:**

1. **ساخت اکانت در Render:**
   - به [render.com](https://render.com) برید و ثبت‌نام کنید
   - اکانت GitHub خود را متصل کنید

2. **ساخت PostgreSQL Database:**
   - New → PostgreSQL
   - نام: `election-bot-db`
   - پلن: Free
   - Internal Database URL را کپی کنید

3. **ساخت Web Service:**
   - New → Web Service
   - مخزن GitHub را انتخاب کنید
   - تنظیمات:
     - **Name:** `election-bot-system`
     - **Environment:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn wsgi:app --bind 0.0.0.0:$PORT`

4. **تنظیم Environment Variables:**
   ```
   DATABASE_URI=<postgresql-url-from-step-2>
   ADMIN_SECRET_KEY=<random-secret-key>
   CANDIDATE_SECRET_KEY=<random-secret-key>
   ```

5. **مقداردهی اولیه دیتابیس:**
   - Shell را باز کنید
   - دستور `python init_db.py` را اجرا کنید

---

### 2️⃣ Railway.app

**مزایا:**
- ✅ رایگان تا $5 ماهیانه
- ✅ راه‌اندازی بسیار آسان
- ✅ PostgreSQL رایگان

**مراحل:**

1. به [railway.app](https://railway.app) برید
2. New Project → Deploy from GitHub repo
3. مخزن را انتخاب کنید
4. Add PostgreSQL
5. Variables را تنظیم کنید:
   ```
   DATABASE_URI=${{Postgres.DATABASE_URL}}
   ADMIN_SECRET_KEY=<random>
   CANDIDATE_SECRET_KEY=<random>
   ```

---

### 3️⃣ Fly.io

**مزایا:**
- ✅ رایگان برای استارت
- ✅ سرعت بالا
- ✅ دیتاسنترهای مختلف

**مراحل:**

1. نصب Fly CLI:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. ورود:
   ```bash
   fly auth login
   ```

3. راه‌اندازی:
   ```bash
   fly launch
   fly secrets set ADMIN_SECRET_KEY=<random>
   fly secrets set CANDIDATE_SECRET_KEY=<random>
   fly deploy
   ```

---

## ⚙️ تنظیمات پس از دیپلوی

### 1. مقداردهی دیتابیس
از Shell سرور دستور زیر را اجرا کنید:
```bash
python init_db.py
```

### 2. ورود به پنل ادمین
- آدرس: `https://your-app.com/admin`
- نام کاربری: `admin`
- رمز عبور: `admin123`

⚠️ **حتماً رمز عبور ادمین را تغییر دهید!**

### 3. ساخت بات در BotFather
1. به `@BotFather` در تلگرام پیام دهید
2. دستور `/newbot` را بزنید
3. توکن را دریافت کنید
4. در پنل ادمین بات را راه‌اندازی کنید

---

## 🔒 نکات امنیتی

1. **SECRET_KEY ها را تغییر دهید**
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```

2. **رمز عبور ادمین را تغییر دهید**

3. **توکن بات را محرمانه نگه دارید**

4. **از HTTPS استفاده کنید** (اتوماتیک در Render)

---

## 📊 مانیتورینگ

- **Logs:** در پنل Render → Logs
- **Database:** در پنل Render → PostgreSQL → Metrics
- **Uptime:** استفاده از UptimeRobot.com

---

## 🆘 عیب‌یابی

### بات کار نمی‌کنه
- چک کنید توکن صحیح باشد
- لاگ‌ها را بررسی کنید
- مطمئن شوید دیتابیس متصل است

### خطای Database Connection
- DATABASE_URI را چک کنید
- مطمئن شوید PostgreSQL فعال است
- SSL mode را چک کنید

### خطای Memory
- تعداد workers gunicorn را کم کنید
- از Render پلن بهتر استفاده کنید

---

## 📞 پشتیبانی

اگر مشکلی داشتید:
1. Issues در GitHub
2. لاگ‌های سرور را بررسی کنید
3. Documentation را مطالعه کنید

</div>
