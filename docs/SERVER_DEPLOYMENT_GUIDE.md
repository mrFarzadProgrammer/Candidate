# 🚀 راهنمای کامل Deployment روی سرور لینوکس

## 📋 مشخصات سرور شما:
```
IP: 78.39.57.188
User: root
Pass: xOqyF28i75
OS: Linux (IRNVMe-1)
```

---

## 🎯 مرحله 1: اتصال به سرور

### از ویندوز (با PuTTY یا PowerShell):

#### روش 1: با PowerShell
```powershell
ssh root@78.39.57.188
# وقتی پسورد خواست: xOqyF28i75
```

#### روش 2: با PuTTY
1. دانلود PuTTY: https://www.putty.org/
2. باز کردن PuTTY
3. در قسمت Host Name: `78.39.57.188`
4. Port: `22`
5. کلیک روی Open
6. Username: `root`
7. Password: `xOqyF28i75`

---

## 🎯 مرحله 2: آپلود فایل Deploy Script

### روش 1: با Git (ساده‌ترین)
```bash
# روی سرور این دستورات رو اجرا کن:
cd /root
git clone https://github.com/mrFarzadProgrammer/Candidate.git
cd Candidate
```

### روش 2: با SCP (اگر git نداری)
```powershell
# روی کامپیوتر خودت (ویندوز):
scp -r C:\Workspace\candidate root@78.39.57.188:/root/
```

---

## 🎯 مرحله 3: اجرای اسکریپت Deploy

```bash
# روی سرور:
cd /root/Candidate/deployment
chmod +x deploy_server.sh
./deploy_server.sh
```

این اسکریپت خودش همه چیز رو انجام میده:
- ✅ نصب Python و ابزارهای لازم
- ✅ ایجاد Virtual Environment
- ✅ نصب تمام پکیج‌ها
- ✅ اجرای Migration‌های دیتابیس
- ✅ پیکربندی Nginx
- ✅ پیکربندی Supervisor (برای مدیریت Process‌ها)
- ✅ راه‌اندازی تمام سرویس‌ها

---

## 🎯 مرحله 4: تست و بررسی

### بررسی وضعیت سرویس‌ها:
```bash
supervisorctl status
```

باید خروجی شبیه این باشه:
```
candidate-admin     RUNNING   pid 1234, uptime 0:01:23
candidate-panel     RUNNING   pid 1235, uptime 0:01:23
candidate-bot       RUNNING   pid 1236, uptime 0:01:23
```

### مشاهده لاگ‌ها:
```bash
# لاگ Admin Panel
tail -f /var/log/candidate-admin.out.log

# لاگ Candidate Panel
tail -f /var/log/candidate-panel.out.log

# لاگ Telegram Bot
tail -f /var/log/candidate-bot.out.log
```

### تست اتصال:
```bash
# تست Admin Panel
curl http://localhost:5000

# تست Candidate Panel
curl http://localhost:5001
```

---

## 🌐 دسترسی به پنل‌ها

بعد از deploy موفق، می‌تونی از این آدرس‌ها استفاده کنی:

- **Admin Panel**: http://78.39.57.188/admin/
- **Candidate Panel**: http://78.39.57.188/candidate/

---

## 🔧 دستورات مفید مدیریت

### مدیریت سرویس‌ها:
```bash
# ریستارت همه سرویس‌ها
supervisorctl restart all

# ریستارت Admin Panel
supervisorctl restart candidate-admin

# ریستارت Candidate Panel
supervisorctl restart candidate-panel

# ریستارت Bot
supervisorctl restart candidate-bot

# استاپ همه
supervisorctl stop all

# استارت همه
supervisorctl start all
```

### مشاهده لاگ‌ها (زنده):
```bash
tail -f /var/log/candidate-admin.out.log
tail -f /var/log/candidate-panel.out.log
tail -f /var/log/candidate-bot.out.log
```

### بررسی Nginx:
```bash
# چک کردن پیکربندی
nginx -t

# ریستارت Nginx
systemctl restart nginx

# مشاهده لاگ‌های Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### آپدیت کد (بعد از push جدید):
```bash
cd /root/Candidate
git pull origin main
pip install -r requirements.txt
supervisorctl restart all
```

---

## 🐛 عیب‌یابی (اگر مشکلی پیش اومد)

### اگر سرویسی STOPPED شد:
```bash
# مشاهده خطا
tail -100 /var/log/candidate-admin.err.log
tail -100 /var/log/candidate-panel.err.log
tail -100 /var/log/candidate-bot.err.log

# ریستارت سرویس
supervisorctl restart candidate-admin
```

### اگر Nginx خطا داد:
```bash
nginx -t  # چک کردن پیکربندی
systemctl status nginx
tail -50 /var/log/nginx/error.log
```

### اگر دیتابیس خطا داد:
```bash
cd /root/Candidate
source venv/bin/activate
python scripts/migrate_gamification.py
python scripts/migrate_ai_features.py
```

### بررسی پورت‌ها:
```bash
netstat -tlnp | grep :5000
netstat -tlnp | grep :5001
netstat -tlnp | grep :80
```

---

## 🔐 امنیت (بعد از Deploy)

### تغییر پسورد root:
```bash
passwd
```

### فعال کردن Firewall:
```bash
ufw status  # بررسی وضعیت
# firewall در اسکریپت deploy فعال شده
```

### ایجاد یوزر جدید (به جای root):
```bash
adduser candidate
usermod -aG sudo candidate
# بعد با این یوزر کار کن به جای root
```

---

## 📞 اگر مشکلی داشتی

1. لاگ‌ها رو چک کن
2. وضعیت سرویس‌ها رو ببین: `supervisorctl status`
3. Nginx رو بررسی کن: `nginx -t`
4. اگر حل نشد، لاگ‌های خطا رو بفرست

---

## ✅ چک‌لیست نهایی

- [ ] اتصال SSH موفق
- [ ] اجرای deploy_server.sh موفق
- [ ] همه سرویس‌ها RUNNING هستند
- [ ] Admin Panel در مرورگر باز می‌شود
- [ ] Candidate Panel در مرورگر باز می‌شود
- [ ] Bot به پیام‌ها پاسخ می‌دهد
- [ ] لاگ‌ها خطایی ندارند

---

موفق باشی! 🚀
