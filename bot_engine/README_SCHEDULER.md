# 🤖 Post Scheduler - سیستم ارسال خودکار پست

## نصب

```bash
pip install schedule requests
```

## استفاده

### 1. اجرای Standalone

```bash
python bot_engine/post_scheduler.py
```

### 2. استفاده در کد

```python
from bot_engine.post_scheduler import start_scheduler

# شروع scheduler
start_scheduler()
```

## ویژگی‌ها

✅ **ارسال خودکار** - هر 1 دقیقه چک می‌کند
✅ **Retry Mechanism** - 3 بار تلاش مجدد
✅ **Error Handling** - مدیریت کامل خطاها
✅ **Logging** - ثبت تمام رویدادها
✅ **Media Support** - text, photo, video, document
✅ **Pin Messages** - پین خودکار پیام
✅ **Cleanup** - حذف خودکار پست‌های قدیمی

## تنظیمات

| پارامتر | مقدار پیش‌فرض | توضیحات |
|---------|---------------|---------|
| Check Interval | 1 minute | فاصله بررسی پست‌ها |
| Max Retry | 3 | تعداد تلاش مجدد |
| Retry Delay | 5 minutes | فاصله بین retry ها |
| Cleanup Days | 30 days | حذف پست‌های قدیمی‌تر از |

## لاگ‌ها

```bash
# مشاهده لاگ‌های زنده
tail -f post_scheduler.log

# جستجو در لاگ‌ها
grep "ERROR" post_scheduler.log

# آخرین 100 خط
tail -n 100 post_scheduler.log
```

## وضعیت‌های پست

- `pending` - در انتظار ارسال
- `sent` - ارسال شده
- `failed` - ارسال ناموفق (بعد از 3 تلاش)
- `cancelled` - لغو شده توسط کاربر

## مثال

```python
from database.models import ScheduledPost
from datetime import datetime, timedelta

# ایجاد پست جدید
post = ScheduledPost(
    channel_id=1,
    candidate_id=1,
    content="سلام! این یک پست تست است.",
    scheduled_time=datetime.utcnow() + timedelta(hours=1),
    status='pending'
)

db.session.add(post)
db.session.commit()

# Scheduler خودکار آن را ارسال می‌کند!
```

## Production

برای Production از supervisor یا systemd استفاده کنید:

```ini
[program:post_scheduler]
command=python /path/to/bot_engine/post_scheduler.py
directory=/path/to/candidate
autostart=true
autorestart=true
stderr_logfile=/var/log/post_scheduler.err.log
stdout_logfile=/var/log/post_scheduler.out.log
```

## Support

راهنمای کامل: `docs/CHANNEL_MANAGEMENT_GUIDE.md`
