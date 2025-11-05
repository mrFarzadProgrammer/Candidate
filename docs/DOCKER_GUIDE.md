# 🐳 راهنمای سریع Docker

## 🚀 راه‌اندازی با Docker (پیشنهادی برای Production)

### پیش‌نیاز:
```powershell
# نصب Docker Desktop از:
# https://www.docker.com/products/docker-desktop
```

### گام 1: تنظیم متغیرهای محیطی

```powershell
# کپی فایل نمونه
Copy-Item .env.example .env

# ویرایش
notepad .env
```

محتوای `.env`:
```env
DATABASE_URI=postgresql://election_user:election_pass_2025@postgres:5432/election_bot
ADMIN_SECRET_KEY=your-super-secret-admin-key-change-this
CANDIDATE_SECRET_KEY=your-super-secret-candidate-key-change-this
```

### گام 2: بیلد و اجرا

```powershell
# بیلد image ها
docker-compose build

# راه‌اندازی همه سرویس‌ها
docker-compose up -d

# مشاهده وضعیت
docker-compose ps
```

خروجی باید شبیه این باشه:
```
NAME                  COMMAND                  SERVICE             STATUS
election_admin        "python -c 'from adm…"   admin_panel         Up
election_bots         "python bot_runner.py"   bot_manager         Up
election_candidate    "python -c 'from can…"   candidate_panel     Up
election_db           "docker-entrypoint.s…"   postgres            Up (healthy)
```

### گام 3: مقداردهی دیتابیس

```powershell
docker-compose exec admin_panel python init_db.py
```

### گام 4: دسترسی

- **پنل ادمین**: http://localhost:5000
- **پنل نماینده**: http://localhost:5001
- **دیتابیس**: localhost:5432

### مشاهده لاگ‌ها

```powershell
# همه سرویس‌ها
docker-compose logs -f

# فقط بات‌ها
docker-compose logs -f bot_manager

# فقط پنل ادمین
docker-compose logs -f admin_panel
```

### توقف و پاکسازی

```powershell
# توقف سرویس‌ها
docker-compose stop

# حذف کانتینرها (داده‌ها حفظ می‌شود)
docker-compose down

# حذف کامل شامل volumes
docker-compose down -v
```

---

## 🌐 استقرار چند سروری (Multi-Host)

### سناریو: 3 سرور

#### سرور 1 (دیتابیس و پنل‌ها):
```bash
# فقط دیتابیس و پنل‌ها
docker-compose up -d postgres admin_panel candidate_panel
```

#### سرور 2 و 3 (بات‌ها):
```bash
# فقط بات‌ها
docker-compose up -d bot_manager
```

در `.env` سرور 2 و 3:
```env
DATABASE_URI=postgresql://election_user:pass@IP_SERVER_1:5432/election_bot
```

---

## 📊 مانیتورینگ

### وضعیت سرویس‌ها:
```powershell
docker-compose ps
```

### مصرف منابع:
```powershell
docker stats
```

### ورود به کانتینر:
```powershell
docker-compose exec admin_panel bash
```

---

## 🔄 بروزرسانی

```powershell
# دریافت آخرین تغییرات
git pull

# بیلد مجدد
docker-compose build

# راه‌اندازی مجدد
docker-compose up -d
```

---

## 💾 Backup

### دیتابیس:
```powershell
docker-compose exec postgres pg_dump -U election_user election_bot > backup.sql
```

### Restore:
```powershell
docker-compose exec -T postgres psql -U election_user election_bot < backup.sql
```

---

## ⚡ نکات بهینه‌سازی

### استفاده از Redis برای Cache:
در `docker-compose.yml` اضافه کنید:
```yaml
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Nginx برای Load Balancing:
```yaml
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

---

## 🐛 عیب‌یابی

### بات کار نمی‌کند:
```powershell
# بررسی لاگ
docker-compose logs bot_manager

# ریستارت
docker-compose restart bot_manager
```

### دیتابیس متصل نمی‌شود:
```powershell
# بررسی health
docker-compose ps postgres

# اتصال دستی
docker-compose exec postgres psql -U election_user -d election_bot
```

### پورت اشغال است:
```powershell
# تغییر پورت در docker-compose.yml
ports:
  - "5002:5000"  # پورت 5002 روی هاست
```

---

این Docker setup کاملاً آماده production است! 🚀
