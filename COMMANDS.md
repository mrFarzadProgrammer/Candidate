# دستورات مفید برای توسعه و مدیریت

## راه‌اندازی محیط توسعه

```powershell
# ایجاد و فعال‌سازی محیط مجازی
python -m venv venv
.\venv\Scripts\Activate.ps1

# نصب وابستگی‌ها
pip install -r requirements.txt

# نصب ابزارهای توسعه
pip install black flake8 pytest
```

## مدیریت دیتابیس

```powershell
# مقداردهی اولیه
python init_db.py

# حذف و بازسازی دیتابیس
Remove-Item election_bot.db
python init_db.py

# ورود به کنسول Python برای کار با دیتابیس
python
```

در کنسول Python:
```python
from admin_panel.app import app, db
from database.models import *

with app.app_context():
    # مشاهده همه نماینده‌ها
    candidates = Candidate.query.all()
    for c in candidates:
        print(f"{c.id}: {c.full_name}")
    
    # مشاهده پلن‌ها
    plans = Plan.query.all()
    for p in plans:
        print(f"{p.name}: {p.price}")
    
    # اضافه کردن نماینده جدید
    from werkzeug.security import generate_password_hash
    new_candidate = Candidate(
        username='test',
        password=generate_password_hash('test123'),
        full_name='نماینده تست',
        city='تهران'
    )
    db.session.add(new_candidate)
    db.session.commit()
```

## اجرای سرورها

```powershell
# همه سرویس‌ها
python main.py

# فقط پنل ادمین
python admin_panel/app.py

# فقط پنل نماینده
python candidate_panel/app.py
```

## تست

```powershell
# اجرای تست‌ها
pytest

# تست با coverage
pytest --cov=.

# تست یک فایل خاص
pytest tests/test_models.py
```

## کد استایل

```powershell
# فرمت کردن کد
black .

# بررسی کد
flake8 .
```

## Git Commands

```powershell
# اولین commit
git add .
git commit -m "Initial commit: Election bot management system"
git push origin main

# ایجاد branch جدید برای feature
git checkout -b feature/new-feature
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
```

## دیپلوی (Deployment)

### روی سرور Linux

```bash
# نصب Python و وابستگی‌ها
sudo apt update
sudo apt install python3 python3-pip python3-venv

# کلون پروژه
git clone https://github.com/Farzad93/Cafe_Bots_Project.git
cd candidate

# محیط مجازی
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# تنظیم متغیرهای محیطی
cp .env.example .env
nano .env

# مقداردهی دیتابیس
python init_db.py

# اجرا با systemd یا supervisor
```

### با Docker

```bash
# بیلد image
docker build -t election-bot .

# اجرا
docker run -d -p 5000:5000 -p 5001:5001 election-bot
```

### با Gunicorn (Production)

```powershell
# نصب
pip install gunicorn

# اجرا
gunicorn -w 4 -b 0.0.0.0:5000 admin_panel.app:app
gunicorn -w 4 -b 0.0.0.0:5001 candidate_panel.app:app
```

## Nginx Configuration

```nginx
server {
    listen 80;
    server_name admin.yourdomain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name candidate.yourdomain.com;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## مانیتورینگ و لاگ

```powershell
# مشاهده لاگ‌ها
Get-Content app.log -Tail 50 -Wait

# پاک کردن لاگ‌ها
Remove-Item app.log
```

## Backup

```powershell
# بکاپ دیتابیس
Copy-Item election_bot.db "backup_$(Get-Date -Format 'yyyy-MM-dd').db"

# بکاپ فایل‌های آپلود شده
Compress-Archive -Path uploads -DestinationPath "uploads_backup_$(Get-Date -Format 'yyyy-MM-dd').zip"
```

## Performance

```powershell
# نصب Redis برای کش
pip install redis flask-caching

# استفاده از PostgreSQL به جای SQLite
# در .env:
# DATABASE_URI=postgresql://user:pass@localhost/election_bot
```

## Security Checklist

- [ ] تغییر SECRET_KEY در production
- [ ] تغییر رمز ادمین پیش‌فرض
- [ ] استفاده از HTTPS
- [ ] فعال کردن CORS protection
- [ ] Rate limiting برای API
- [ ] Backup منظم دیتابیس
- [ ] بررسی لاگ‌های امنیتی

## Troubleshooting

### بات کار نمی‌کند
```powershell
# بررسی لاگ
Get-Content app.log | Select-String "error" -Context 2

# تست توکن بات
python -c "from telegram import Bot; bot = Bot('YOUR_TOKEN'); print(bot.get_me())"
```

### خطای دیتابیس
```powershell
# بررسی connection string
python -c "from config.settings import DATABASE_URI; print(DATABASE_URI)"

# تست اتصال
python -c "from database.models import db; from admin_panel.app import app; app.app_context().push(); print(db.engine.execute('SELECT 1').scalar())"
```

### مشکل پورت
```powershell
# پیدا کردن پروسه روی پورت
netstat -ano | findstr :5000

# kill کردن پروسه
taskkill /PID <PID> /F
```

## محیط توسعه توصیه شده

- **IDE**: VS Code با افزونه‌های Python، Pylance
- **Database Client**: DB Browser for SQLite یا pgAdmin
- **API Testing**: Postman یا Thunder Client
- **Git Client**: Git Bash یا GitHub Desktop
- **Terminal**: Windows Terminal یا PowerShell

## مستندات مفید

- Flask: https://flask.palletsprojects.com/
- python-telegram-bot: https://docs.python-telegram-bot.org/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Telegram Bot API: https://core.telegram.org/bots/api
