# Load Testing Configuration
# پیکربندی تست بار

## راه‌اندازی سریع

### نصب Locust
```bash
pip install locust
```

### اجرای تست با پارامترها
```bash
# تست با 1000 کاربر - 100 کاربر در ثانیه spawn می‌شن
locust -f locustfile.py --users 1000 --spawn-rate 100 --host http://localhost:5000

# تست با 500 کاربر - مدت زمان 5 دقیقه
locust -f locustfile.py --users 500 --spawn-rate 50 --run-time 5m --host http://localhost:5000

# تست بدون UI (headless)
locust -f locustfile.py --users 1000 --spawn-rate 100 --host http://localhost:5000 --headless
```

### اجرای تست با Web UI
```bash
cd load_tests
locust -f locustfile.py

# باز کردن مرورگر:
http://localhost:8089
```

## انواع کاربران تست

### 1. CandidatePanelUser
- **وزن**: بالا (بیشترین تعداد)
- **عملیات**: مشاهده داشبورد، پیام‌ها، کاربران، پروفایل
- **سناریو**: کاربر معمولی پنل کاندید

### 2. BroadcastUser
- **وزن**: متوسط
- **عملیات**: ارسال broadcast به کاربران
- **سناریو**: ارسال پیام جمعی

### 3. MessageReadUser
- **وزن**: بالا
- **عملیات**: خواندن و مارک کردن پیام‌ها
- **سناریو**: پاسخ به پیام‌های کاربران

### 4. AdminPanelUser
- **وزن**: پایین
- **عملیات**: مشاهده داشبورد ادمین، مدیریت کاندیدها، پلن‌ها
- **سناریو**: مدیر سیستم

### 5. DatabaseIntensiveUser
- **وزن**: پایین
- **عملیات**: آنالیتیکس، export داده
- **سناریو**: عملیات سنگین دیتابیس

## سناریوهای تست

### تست 1: بار معمولی (Normal Load)
```bash
locust -f locustfile.py \
  --users 500 \
  --spawn-rate 50 \
  --run-time 10m \
  --host http://localhost:5000
```
- **هدف**: عملکرد در شرایط عادی
- **معیار موفقیت**: 
  - Response time < 500ms
  - Failure rate < 0.1%

### تست 2: بار سنگین (Heavy Load)
```bash
locust -f locustfile.py \
  --users 1000 \
  --spawn-rate 100 \
  --run-time 15m \
  --host http://localhost:5000
```
- **هدف**: تست auto-scaling
- **معیار موفقیت**:
  - Response time < 2000ms
  - Failure rate < 1%
  - Auto-scaling triggers

### تست 3: بار فوق سنگین (Stress Test)
```bash
locust -f locustfile.py \
  --users 2000 \
  --spawn-rate 200 \
  --run-time 20m \
  --host http://localhost:5000
```
- **هدف**: پیدا کردن حد شکست
- **معیار**: تا کجا می‌تونه تحمل کنه

### تست 4: بار ناگهانی (Spike Test)
```bash
# شروع با 100 کاربر
locust -f locustfile.py \
  --users 100 \
  --spawn-rate 100 \
  --host http://localhost:5000

# در حین اجرا spawn rate رو افزایش بده:
# از UI: تغییر به 1000 کاربر با spawn-rate 500
```
- **هدف**: واکنش به افزایش ناگهانی ترافیک
- **معیار**: سیستم نباید crash کنه

## معیارهای موفقیت

### Response Time
- **عالی**: < 500ms
- **خوب**: 500ms - 1000ms
- **قابل قبول**: 1000ms - 2000ms
- **ضعیف**: > 2000ms

### Failure Rate
- **عالی**: < 0.1%
- **خوب**: 0.1% - 0.5%
- **قابل قبول**: 0.5% - 1%
- **ضعیف**: > 1%

### Throughput (RPS - Requests Per Second)
- **مینیمم مورد نیاز**: 100 RPS
- **خوب**: 500 RPS
- **عالی**: 1000+ RPS

### Database Performance
- **Connection Pool**: نباید تمام بشه
- **Query Time**: < 100ms برای query های ساده
- **Deadlocks**: 0

### Redis Performance
- **Memory Usage**: < 80% ظرفیت
- **Response Time**: < 10ms
- **Cache Hit Rate**: > 80%

## مانیتورینگ

### چک‌کردن منابع حین تست

#### CPU Usage
```bash
# لینوکس
top -p $(pgrep -f "python.*app.py")

# ویندوز
# Task Manager -> Details -> python.exe
```

#### Memory Usage
```bash
# لینوکس
ps aux | grep python | grep app.py

# ویندوز  
# Task Manager -> Details -> python.exe -> Memory
```

#### Database Connections
```python
# در psql یا sqlite
SELECT count(*) FROM pg_stat_activity;  # PostgreSQL
```

#### Redis Stats
```bash
redis-cli INFO stats
```

### نمونه Output موفق

```
📊 خلاصه آمار:
   Total Requests: 125000
   Failed Requests: 85
   Average Response Time: 456.32 ms
   Max Response Time: 2341.12 ms
   Min Response Time: 12.45 ms
   Requests/sec: 208.33

✅ SUCCESS: Failure rate is 0.07%
✅ SUCCESS: Average response time is 456.32 ms
```

## عیب‌یابی

### مشکل: Response Time بالا

**راه‌حل‌ها:**
1. بررسی query های دیتابیس (اضافه کردن index)
2. افزایش connection pool
3. استفاده از Redis cache
4. بهینه‌سازی کد پایتون

### مشکل: Failure Rate بالا

**راه‌حل‌ها:**
1. چک کردن لاگ‌های خطا
2. افزایش timeout ها
3. بررسی rate limiting (ممکنه خیلی strict باشه)
4. چک کردن database deadlocks

### مشکل: Memory Leak

**راه‌حل‌ها:**
1. بررسی session management
2. چک کردن database connection leaks
3. استفاده از memory profiler
4. بررسی file handles

## تست Production

### قبل از تست روی Production:

1. **Backup بگیر** از دیتابیس
2. **زمان مناسب** انتخاب کن (خارج از ساعات اوج)
3. **تیم آماده باش** داشته باش
4. **Monitoring فعال** باشه
5. **Rollback plan** داشته باش

### تست روی Production:
```bash
# شروع آرام
locust -f locustfile.py \
  --users 50 \
  --spawn-rate 5 \
  --host https://your-production-url.com

# تدریجی افزایش بده
```

## گزارش نهایی

بعد از تست یه فایل JSON از نتایج بساز:

```bash
locust -f locustfile.py \
  --users 1000 \
  --spawn-rate 100 \
  --run-time 10m \
  --host http://localhost:5000 \
  --html load_test_report.html \
  --csv load_test_results
```

این فایل‌ها رو ذخیره کن:
- `load_test_report.html` - گزارش بصری
- `load_test_results_stats.csv` - آمار دقیق
- `load_test_results_failures.csv` - لیست خطاها

## بهینه‌سازی پیشنهادی

### دیتابیس
```python
# اضافه کردن index ها
CREATE INDEX idx_message_candidate ON messages(candidate_id);
CREATE INDEX idx_user_telegram ON users(telegram_id);
CREATE INDEX idx_broadcast_status ON broadcasts(status);
```

### Redis Caching
```python
# Cache کردن داده‌های پرتکرار
@app.route('/dashboard')
@cache.cached(timeout=60)
def dashboard():
    # ...
```

### Connection Pooling
```python
# تنظیمات SQLAlchemy
app.config['SQLALCHEMY_POOL_SIZE'] = 20
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 40
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800
```

### Auto-Scaling (با Docker)
```yaml
# docker-compose.yml
services:
  web:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
      restart_policy:
        condition: on-failure
```

## چک‌لیست قبل از Production

- [ ] Load test با 1000+ کاربر موفق
- [ ] Response time < 2s
- [ ] Failure rate < 1%
- [ ] Auto-scaling تست شده
- [ ] Database indexes اضافه شده
- [ ] Redis caching فعال
- [ ] Connection pooling پیکربندی شده
- [ ] Error handling کامل
- [ ] Monitoring نصب شده
- [ ] Backup strategy موجود
- [ ] Rollback plan آماده

---

**نکته مهم**: همیشه ابتدا روی staging test کن، سپس production!
