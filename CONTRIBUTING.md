# 🔧 راهنمای توسعه‌دهندگان

<div dir="rtl">

## 🏁 شروع سریع برای Development

### نصب و راه‌اندازی

```bash
# Clone کردن پروژه
git clone https://github.com/YOUR_USERNAME/election-bot-system.git
cd election-bot-system

# ساخت محیط مجازی
python -m venv .venv

# فعال‌سازی (Windows)
.venv\Scripts\activate

# فعال‌سازی (Linux/Mac)
source .venv/bin/activate

# نصب dependencies
pip install -r requirements.txt

# مقداردهی دیتابیس
python init_db.py

# اجرای پروژه
python main.py
```

### دسترسی به پنل‌ها:
- پنل ادمین: http://localhost:5000
- پنل نماینده: http://localhost:5001

ورود ادمین: `admin` / `admin123`

---

## 📁 ساختار پروژه

```
election-bot-system/
├── admin_panel/          # پنل سوپر ادمین
│   └── app.py           # Flask app پنل ادمین
├── candidate_panel/      # پنل نماینده
│   └── app.py           # Flask app پنل نماینده
├── bot_engine/          # موتور بات تلگرام
│   ├── bot_manager.py   # مدیریت چند بات همزمان
│   └── telegram_bot.py  # لاجیک بات تلگرام
├── database/            # مدل‌های دیتابیس
│   └── models.py        # SQLAlchemy models
├── config/              # تنظیمات
│   └── settings.py      # کانفیگ اصلی
├── templates/           # قالب‌های HTML
│   ├── admin/          # قالب‌های پنل ادمین
│   └── candidate/      # قالب‌های پنل نماینده
├── static/             # فایل‌های استاتیک
│   └── css/           # استایل‌ها
├── uploads/            # آپلودهای کاربران
├── main.py            # نقطه ورود اصلی
├── wsgi.py            # WSGI entry point for production
└── requirements.txt    # Dependencies
```

---

## 🔄 Git Workflow

### برای آپدیت کردن کد:

```bash
# تغییرات جدید
git add .
git commit -m "توضیح تغییرات"
git push origin main
```

یا استفاده از اسکریپت آماده:
```bash
# Windows
push_to_github.bat

# Linux/Mac
./push_to_github.sh
```

### برای دریافت آخرین تغییرات:
```bash
git pull origin main
```

---

## 🗄️ کار با Database

### SQLite (Development)
```python
# در config/settings.py
DATABASE_URI = 'sqlite:///election_bot.db'
```

### PostgreSQL (Production)
```python
# در config/settings.py یا Environment Variable
DATABASE_URI = 'postgresql://user:pass@host:5432/dbname'
```

### مقداردهی مجدد:
```bash
python init_db.py
```

---

## 🤖 توسعه بات تلگرام

### ساختار handlers:
```python
# در bot_engine/telegram_bot.py

async def start_command(update, context):
    """دستور /start"""
    pass

async def button_callback(update, context):
    """کلیک روی دکمه‌ها"""
    pass

async def handle_message(update, context):
    """پیام‌های متنی"""
    pass
```

### افزودن امکان جدید:
1. Model مربوطه را در `database/models.py` بسازید
2. Route مربوطه را در پنل نماینده اضافه کنید
3. Handler مربوطه را در بات اضافه کنید

---

## 🎨 توسعه Frontend

### استایل‌ها:
- همه در `static/css/style.css`
- RTL support
- Responsive design

### قالب‌ها:
- Jinja2 templates
- Base templates برای هر پنل
- Component-based structure

---

## 🧪 تست

### اجرای تست‌ها:
```bash
pytest
```

### تست دستی:
```bash
# تست لاگین نماینده
python test_login.py

# بررسی وضعیت بات
python check_bot_status.py

# مدیریت نمایندگان
python manage_candidates.py
```

---

## 📦 افزودن Feature جدید

### مثال: اضافه کردن "نظرسنجی"

1. **Model:**
```python
# database/models.py
class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    question = db.Column(db.String(500))
    # ...
```

2. **Route در پنل نماینده:**
```python
# candidate_panel/app.py
@app.route('/polls')
@login_required
def polls():
    # ...
```

3. **Template:**
```html
<!-- templates/candidate/polls.html -->
```

4. **Handler در بات:**
```python
# bot_engine/telegram_bot.py
async def show_polls(update, context):
    # ...
```

5. **Migration:**
```bash
python init_db.py  # یا از Alembic استفاده کنید
```

---

## 🐛 Debug

### لاگ‌های بات:
```python
print(f"🔍 Debug info: {variable}")
```

### لاگ‌های Flask:
```python
app.logger.info("Log message")
```

### دیباگ دیتابیس:
```bash
# Shell
python
>>> from database.models import *
>>> Candidate.query.all()
```

---

## 📚 منابع مفید

- [Flask Documentation](https://flask.palletsprojects.com/)
- [python-telegram-bot Docs](https://docs.python-telegram-bot.org/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Jinja2 Templates](https://jinja.palletsprojects.com/)

---

## 💡 Tips & Tricks

### Virtual Environment
همیشه در venv کار کنید:
```bash
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### Git Ignore
قبل از commit مطمئن شوید:
- `*.db` در `.gitignore` است
- `__pycache__` commit نشده
- `.env` commit نشده

### Secret Keys
برای تولید کلید امنیتی:
```bash
python generate_secrets.py
```

### Database Backup
```bash
# SQLite
cp election_bot.db election_bot.db.backup

# PostgreSQL
pg_dump dbname > backup.sql
```

---

## 🤝 مشارکت

1. Fork کنید
2. Branch جدید بسازید (`git checkout -b feature/AmazingFeature`)
3. Commit کنید (`git commit -m 'Add some AmazingFeature'`)
4. Push کنید (`git push origin feature/AmazingFeature`)
5. Pull Request باز کنید

---

## 📞 پشتیبانی

- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Email:** your-email@example.com

</div>
