# دستورات دیپلوی سیستم مدیریت انتخابات
# به ترتیب این دستورات را در سرور اجرا کنید

## 1️⃣ اتصال به سرور
```bash
ssh root@78.39.57.188
# Password: xOqyF28i75
```

## 2️⃣ نصب و راه‌اندازی (روش سریع)
```bash
# دانلود و اجرای اسکریپت
curl -sSL https://raw.githubusercontent.com/mrFarzadProgrammer/Candidate/main/scripts/deploy.sh | bash
```

## 3️⃣ بررسی وضعیت سرویس‌ها
```bash
# بررسی وضعیت
systemctl status election-admin
systemctl status election-candidate
systemctl status election-bot
systemctl status nginx

# مشاهده لاگ‌ها
journalctl -u election-admin -f
journalctl -u election-candidate -f
journalctl -u election-bot -f
```

## 4️⃣ دسترسی به پنل‌ها
- 🔐 **پنل ادمین:** http://78.39.57.188/admin/
  - کاربری: `nasrinjoon`
  - رمز: `myDream220321!`

- 👤 **پنل نماینده:** http://78.39.57.188/
  - (پس از ایجاد نماینده از پنل ادمین)

- 🤖 **بات تلگرام:** @saman_rahjou_bot

## 5️⃣ دستورات مفید

### راه‌اندازی مجدد
```bash
systemctl restart election-admin election-candidate election-bot
```

### متوقف کردن
```bash
systemctl stop election-admin election-candidate election-bot
```

### به‌روزرسانی پروژه
```bash
cd /var/www/candidate
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart election-admin election-candidate election-bot
```

### پاک‌سازی و نصب مجدد
```bash
systemctl stop election-admin election-candidate election-bot
rm -rf /var/www/candidate
# سپس اسکریپت deploy را دوباره اجرا کنید
```

## 6️⃣ عیب‌یابی

### اگر بات کار نمی‌کند:
```bash
journalctl -u election-bot -n 50
# بررسی لاگ‌ها
```

### اگر پنل‌ها لود نمی‌شوند:
```bash
nginx -t
systemctl status nginx
journalctl -u election-admin -n 50
```

### تست دستی
```bash
cd /var/www/candidate
source venv/bin/activate
python3 run_bot.py  # تست بات
python3 -m flask --app admin_panel.app run  # تست ادمین
```

## 7️⃣ تنظیمات امنیتی (اختیاری)

### نصب SSL با Let's Encrypt
```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
systemctl reload nginx
```

### تغییر رمز دیتابیس
```python
cd /var/www/candidate
source venv/bin/activate
python3
>>> from admin_panel.app import app, db
>>> from database.models import Admin
>>> from werkzeug.security import generate_password_hash
>>> with app.app_context():
...     admin = Admin.query.filter_by(username='nasrinjoon').first()
...     admin.password = generate_password_hash('NEW_PASSWORD')
...     db.session.commit()
```

## 8️⃣ بکاپ گیری

### بکاپ دیتابیس
```bash
cp /var/www/candidate/instance/election.db /root/backup-$(date +%Y%m%d).db
```

### بکاپ کامل
```bash
tar -czf /root/candidate-backup-$(date +%Y%m%d).tar.gz /var/www/candidate
```

---

## ✅ چک‌لیست نهایی
- [ ] سرویس‌ها active هستند
- [ ] پنل ادمین قابل دسترسی است
- [ ] پنل نماینده قابل دسترسی است
- [ ] بات تلگرام پاسخ می‌دهد
- [ ] فایروال فعال است
- [ ] Nginx بدون خطا کار می‌کند

**پشتیبانی:** در صورت بروز مشکل، لاگ‌ها را با `journalctl` بررسی کنید.
