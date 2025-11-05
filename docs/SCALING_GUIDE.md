# 🚀 راهنمای مقیاس‌پذیری و توزیع بات‌ها

<div dir="rtl">

## 🎯 مشکل: وقتی بات‌ها زیاد شدند چه کار کنیم؟

وقتی تعداد نماینده‌ها و بات‌ها زیاد می‌شه (مثلاً 100+ بات)، نمی‌شه همه رو روی یک سرور اجرا کرد. باید توزیع بشن!

---

## 🏗️ معماری پیشنهادی: Multi-Host با دیتابیس مرکزی

```
                    ┌─────────────────┐
                    │  دیتابیس مرکزی  │
                    │   PostgreSQL    │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │ هاست 1  │         │ هاست 2  │         │ هاست 3  │
   │ بات 1-30│         │ بات31-60│         │ بات61-90│
   └─────────┘         └─────────┘         └─────────┘
```

---

## 📦 راه حل 1: Docker Compose برای شروع

### استفاده:

```bash
# راه‌اندازی کل سیستم
docker-compose up -d

# مشاهده لاگ‌ها
docker-compose logs -f

# توقف
docker-compose down
```

### سرویس‌ها:
- **postgres**: دیتابیس PostgreSQL
- **admin_panel**: پنل مدیریت (پورت 5000)
- **candidate_panel**: پنل نماینده (پورت 5001)
- **bot_manager**: اجرای همه بات‌ها

---

## 🌐 راه حل 2: چند سرور + دیتابیس مرکزی

### هاست 1 (سرور اصلی):
```bash
# نصب PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# تنظیم PostgreSQL برای دسترسی از راه دور
sudo nano /etc/postgresql/15/main/postgresql.conf
# listen_addresses = '*'

sudo nano /etc/postgresql/15/main/pg_hba.conf
# host all all 0.0.0.0/0 md5

sudo systemctl restart postgresql

# ایجاد دیتابیس و کاربر
sudo -u postgres psql
CREATE DATABASE election_bot;
CREATE USER election_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE election_bot TO election_user;
```

### هاست 2، 3، 4 (سرورهای بات):
```bash
# کلون پروژه
git clone https://github.com/Farzad93/Cafe_Bots_Project.git
cd candidate

# محیط مجازی
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# تنظیم .env
cat > .env << EOF
DATABASE_URI=postgresql://election_user:password@IP_SERVER_1:5432/election_bot
ADMIN_SECRET_KEY=your-secret-key
CANDIDATE_SECRET_KEY=your-secret-key
EOF

# اجرای فقط بات‌ها
python bot_runner.py
```

---

## 🎛️ راه حل 3: Load Balancer برای بات‌ها

### ایجاد فایل `bot_distributor.py`:

```python
"""
توزیع‌کننده بات‌ها بین چند هاست
"""
from database.models import BotInstance, BotHost
from sqlalchemy.orm import Session

class BotDistributor:
    def __init__(self, session: Session):
        self.session = session
    
    def assign_bot_to_host(self, bot_id: int):
        """تخصیص بات به کم‌بارترین هاست"""
        hosts = self.session.query(BotHost).all()
        
        # پیدا کردن هاست با کمترین بات
        min_load_host = min(hosts, key=lambda h: h.active_bots_count)
        
        bot = self.session.query(BotInstance).get(bot_id)
        bot.assigned_host_id = min_load_host.id
        
        self.session.commit()
        return min_load_host
    
    def rebalance_bots(self):
        """توزیع مجدد بات‌ها برای تعادل بار"""
        hosts = self.session.query(BotHost).all()
        bots = self.session.query(BotInstance).filter_by(is_active=True).all()
        
        bots_per_host = len(bots) // len(hosts)
        
        for i, bot in enumerate(bots):
            host_index = i // bots_per_host
            bot.assigned_host_id = hosts[host_index].id
        
        self.session.commit()
```

### اضافه کردن جدول BotHost به models.py:

```python
class BotHost(db.Model):
    """سرورهای میزبان بات"""
    __tablename__ = 'bot_hosts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(50))
    max_bots = db.Column(db.Integer, default=30)
    active_bots_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    last_heartbeat = db.Column(db.DateTime)
```

---

## 🔧 راه حل 4: Kubernetes برای مقیاس بالا

### فایل `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: election-bot-deployment
spec:
  replicas: 3  # تعداد پادها
  selector:
    matchLabels:
      app: election-bot
  template:
    metadata:
      labels:
        app: election-bot
    spec:
      containers:
      - name: bot-runner
        image: your-registry/election-bot:latest
        env:
        - name: DATABASE_URI
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: uri
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: election-bot-service
spec:
  selector:
    app: election-bot
  ports:
  - port: 5000
    targetPort: 5000
```

استفاده:
```bash
kubectl apply -f k8s-deployment.yaml
kubectl scale deployment election-bot-deployment --replicas=10
```

---

## 📊 راه حل 5: سیستم صف (Queue) برای عملیات سنگین

### استفاده از Celery + Redis:

```bash
pip install celery redis
```

### فایل `tasks.py`:

```python
from celery import Celery
from database.models import BotInstance, Message

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def send_mass_message(bot_id, message_text, user_ids):
    """ارسال پیام انبوه به صورت async"""
    bot = BotInstance.query.get(bot_id)
    
    for user_id in user_ids:
        try:
            # ارسال پیام
            bot.send_message(user_id, message_text)
        except:
            continue
    
    return f"Sent to {len(user_ids)} users"

@app.task
def process_analytics():
    """پردازش آمار به صورت async"""
    # محاسبات سنگین
    pass
```

### استفاده:
```python
# در جای دیگر از کد
from tasks import send_mass_message

send_mass_message.delay(bot_id=1, message_text="سلام", user_ids=[...])
```

---

## 🔐 راه حل 6: امنیت ارتباط بین سرورها

### استفاده از VPN یا SSH Tunnel:

```bash
# روی سرور بات
ssh -L 5432:localhost:5432 user@database-server
```

یا استفاده از **WireGuard VPN**:

```bash
# نصب
sudo apt install wireguard

# تنظیم
sudo wg-quick up wg0
```

---

## 📈 مانیتورینگ و مدیریت

### Prometheus + Grafana:

```python
# metrics.py
from prometheus_client import Counter, Gauge, start_http_server

bot_messages_total = Counter('bot_messages_total', 'Total messages')
active_bots = Gauge('active_bots', 'Number of active bots')

# در کد
bot_messages_total.inc()
active_bots.set(bot_manager.get_active_bots_count())

# شروع سرور متریک
start_http_server(8000)
```

---

## 🎯 پیاده‌سازی عملی: سناریو 100 بات

### سناریو: 3 سرور

**سرور 1 (مرکزی)**:
- PostgreSQL
- پنل ادمین
- پنل نماینده
- Redis (اختیاری)

**سرور 2**:
- 50 بات اول

**سرور 3**:
- 50 بات دوم

### دستورات:

```bash
# سرور 1
docker-compose up -d postgres admin_panel candidate_panel

# سرور 2
DATABASE_URI=postgresql://user:pass@server1:5432/election_bot \
BOT_ID_RANGE=1-50 \
python bot_runner_range.py

# سرور 3
DATABASE_URI=postgresql://user:pass@server1:5432/election_bot \
BOT_ID_RANGE=51-100 \
python bot_runner_range.py
```

---

## 💡 نکات مهم

### ✅ Do's:
- از connection pooling استفاده کن
- بات‌ها را در process های جدا اجرا کن
- از health check برای بات‌ها استفاده کن
- لاگ‌ها را مرکزی جمع کن (ELK Stack)
- Backup منظم از دیتابیس

### ❌ Don'ts:
- همه بات‌ها رو در یک thread نریز
- بدون monitoring سرور نزار
- بدون rate limiting API تلگرام رو صدا نزن
- رمزها رو hardcode نکن

---

## 📦 آماده‌سازی برای Production

### چک‌لیست:

- [ ] PostgreSQL به جای SQLite
- [ ] SECRET_KEY های قوی
- [ ] HTTPS با SSL
- [ ] Firewall تنظیم شده
- [ ] Backup خودکار روزانه
- [ ] Monitoring فعال
- [ ] Log rotation
- [ ] Rate limiting
- [ ] Health checks
- [ ] Documentation

---

## 🚀 شروع سریع با Docker

```bash
# 1. تنظیم متغیرها
cp .env.example .env
nano .env

# 2. بیلد و اجرا
docker-compose build
docker-compose up -d

# 3. مقداردهی دیتابیس
docker-compose exec admin_panel python init_db.py

# 4. مشاهده وضعیت
docker-compose ps

# 5. لاگ‌ها
docker-compose logs -f bot_manager
```

---

## 💰 هزینه‌ها (تخمینی)

| تعداد بات | سرورها | هزینه ماهانه |
|----------|--------|--------------|
| 1-30 | 1 سرور (2GB RAM) | $10-20 |
| 31-100 | 3 سرور | $30-60 |
| 101-500 | 5+ سرور | $100-200 |
| 500+ | Cloud (AWS/GCP) | $500+ |

---

## 📞 پشتیبانی

برای سوالات بیشتر در مورد مقیاص‌پذیری:
- مستندات Docker: https://docs.docker.com
- مستندات Kubernetes: https://kubernetes.io/docs
- تلگرام بات API limits: https://core.telegram.org/bots/faq#my-bot-is-hitting-limits

---

<p align="center">
  <strong>با این راهکارها می‌تونی تا هزاران بات رو مدیریت کنی! 🚀</strong>
</p>

</div>
