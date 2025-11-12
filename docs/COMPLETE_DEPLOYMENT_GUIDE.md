# راهنمای استقرار کامل سیستم انتخاباتی
# Complete Production Deployment Guide

## فهرست مطالب

1. [الزامات سیستمی](#requirements)
2. [نصب Dependencies](#install-dependencies)
3. [پیکربندی امنیتی](#security-config)
4. [استقرار تک سرور](#single-server)
5. [استقرار چند سرور](#multi-server)
6. [مانیتورینگ و Alerting](#monitoring)
7. [Backup و Recovery](#backup)
8. [عیب‌یابی](#troubleshooting)

---

## <a name="requirements"></a>1. الزامات سیستمی

### سرور تک نود (تا 1000 کاربر):
- CPU: 4 Core
- RAM: 8 GB
- Disk: 100 GB SSD
- OS: Ubuntu 22.04 LTS
- Network: 100 Mbps

### سرور چند نود (1000+ کاربر):
- Load Balancer: 2 Core, 4 GB RAM
- App Servers (×3): 4 Core, 8 GB RAM each
- Database: 8 Core, 16 GB RAM
- Redis: 2 Core, 4 GB RAM
- Total Disk: 500 GB SSD

### نرم‌افزارها:
```bash
- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Nginx 1.21+
- Docker 24+ (برای multi-server)
- Docker Compose 2.20+
```

---

## <a name="install-dependencies"></a>2. نصب Dependencies

### گام 1: آپدیت سیستم
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential python3-dev python3-pip \
    postgresql postgresql-contrib redis-server nginx git
```

### گام 2: نصب Docker (برای deployment چند سرور)
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl enable docker
sudo systemctl start docker

# نصب Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### گام 3: کلون پروژه
```bash
cd /opt
sudo git clone <YOUR_REPOSITORY_URL> candidate
cd candidate
sudo chown -R $USER:$USER /opt/candidate
```

### گام 4: Virtual Environment و Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## <a name="security-config"></a>3. پیکربندی امنیتی

### گام 1: ایجاد فایل .env.production
```bash
cp .env.example .env.production
nano .env.production
```

محتوای فایل:
```bash
# Database
DATABASE_URL=postgresql://candidate_user:STRONG_PASSWORD@localhost:5432/candidate_db

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_QUEUE_URL=redis://localhost:6379/1

# Security
SECRET_KEY=<GENERATE_32_BYTE_RANDOM_KEY>
ADMIN_SECRET_KEY=<GENERATE_32_BYTE_RANDOM_KEY>

# Telegram
TELEGRAM_BOT_TOKEN=<YOUR_BOT_TOKEN>

# Encryption
FERNET_KEY=<GENERATE_FERNET_KEY>

# Session
SESSION_TIMEOUT_HOURS=24
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_LOGIN_PER_MINUTE=5

# Admin IP Whitelist (comma-separated)
ADMIN_ALLOWED_IPS=127.0.0.1,<YOUR_OFFICE_IP>

# Monitoring
SENTRY_DSN=<YOUR_SENTRY_DSN>

# Production Mode
FLASK_ENV=production
DEBUG=False
```

### گام 2: تولید کلیدهای امنیتی
```bash
python3 << EOF
import secrets
import base64
from cryptography.fernet import Fernet

print("SECRET_KEY =", secrets.token_hex(32))
print("ADMIN_SECRET_KEY =", secrets.token_hex(32))
print("FERNET_KEY =", Fernet.generate_key().decode())
EOF
```

### گام 3: راه‌اندازی PostgreSQL
```bash
sudo -u postgres psql

CREATE DATABASE candidate_db;
CREATE USER candidate_user WITH PASSWORD 'STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE candidate_db TO candidate_user;
\q
```

### گام 4: مایگریشن دیتابیس
```bash
source venv/bin/activate
python scripts/init_db.py
python scripts/migrate_security_audit.py
python scripts/migrate_vip_tables.py
```

---

## <a name="single-server"></a>4. استقرار تک سرور

### گام 1: پیکربندی Systemd برای Admin Panel
```bash
sudo nano /etc/systemd/system/candidate-admin.service
```

محتوا:
```ini
[Unit]
Description=Candidate Election System - Admin Panel
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/candidate
Environment="PATH=/opt/candidate/venv/bin"
EnvironmentFile=/opt/candidate/.env.production
ExecStart=/opt/candidate/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5001 \
    --timeout 120 \
    --access-logfile /var/log/candidate/admin-access.log \
    --error-logfile /var/log/candidate/admin-error.log \
    admin_panel.app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### گام 2: پیکربندی Systemd برای Candidate Panel
```bash
sudo nano /etc/systemd/system/candidate-panel.service
```

محتوا:
```ini
[Unit]
Description=Candidate Election System - Candidate Panel
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/candidate
Environment="PATH=/opt/candidate/venv/bin"
EnvironmentFile=/opt/candidate/.env.production
ExecStart=/opt/candidate/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5002 \
    --timeout 120 \
    --access-logfile /var/log/candidate/panel-access.log \
    --error-logfile /var/log/candidate/panel-error.log \
    candidate_panel.app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### گام 3: پیکربندی Nginx
```bash
sudo nano /etc/nginx/sites-available/candidate
```

محتوا:
```nginx
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=general:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

# Admin Panel
server {
    listen 80;
    server_name admin.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name admin.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/admin.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Rate Limiting
    limit_req zone=general burst=20 nodelay;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://127.0.0.1:5001/login;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static {
        alias /opt/candidate/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# Candidate Panel
server {
    listen 80;
    server_name panel.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name panel.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/panel.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/panel.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    limit_req zone=general burst=20 nodelay;
    
    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /opt/candidate/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

فعال‌سازی:
```bash
sudo ln -s /etc/nginx/sites-available/candidate /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### گام 4: نصب SSL با Let's Encrypt
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d admin.yourdomain.com -d panel.yourdomain.com
```

### گام 5: راه‌اندازی سرویس‌ها
```bash
# ایجاد دایرکتوری لاگ
sudo mkdir -p /var/log/candidate
sudo chown www-data:www-data /var/log/candidate

# فعال‌سازی و شروع سرویس‌ها
sudo systemctl daemon-reload
sudo systemctl enable candidate-admin candidate-panel
sudo systemctl start candidate-admin candidate-panel

# بررسی وضعیت
sudo systemctl status candidate-admin
sudo systemctl status candidate-panel
```

---

## <a name="multi-server"></a>5. استقرار چند سرور

### معماری پیشنهادی:
```
Internet
   ↓
Load Balancer (Nginx) - 1 server
   ↓
App Servers - 3 servers (Tehran, Isfahan, Other)
   ↓
Database (PostgreSQL) - 1 master + 2 replicas
   ↓
Cache (Redis) - 1 master + 1 replica
```

### گام 1: تنظیم متغیرهای محیطی
```bash
cd /opt/candidate
nano .env.production
```

تغییرات برای multi-server:
```bash
# استفاده از PostgreSQL خارجی
DATABASE_URL=postgresql://user:pass@db-master.internal:5432/candidate_db

# استفاده از Redis خارجی
REDIS_URL=redis://redis-master.internal:6379/0

# فعال‌سازی Geographic Load Balancing
ENABLE_GEO_ROUTING=true
```

### گام 2: استقرار با Docker Compose
```bash
# روی Load Balancer server
docker-compose -f docker-compose.production.yml up -d nginx

# روی هر App Server
docker-compose -f docker-compose.production.yml up -d app

# روی Database server
docker-compose -f docker-compose.production.yml up -d postgres

# روی Cache server
docker-compose -f docker-compose.production.yml up -d redis redis_queue

# روی Monitoring server
docker-compose -f docker-compose.production.yml up -d prometheus grafana
```

### گام 3: پیکربندی Database Replication

**روی Master:**
```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
```
```ini
wal_level = replica
max_wal_senders = 3
wal_keep_size = 64
```

```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
```
```
host replication replicator <REPLICA_IP>/32 md5
```

**روی Replica:**
```bash
pg_basebackup -h <MASTER_IP> -D /var/lib/postgresql/14/main -U replicator -P -v -R
```

### گام 4: تست Load Balancing
```bash
# نصب ابزار تست
pip install locust

# ساخت فایل تست
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class CandidateUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def index(self):
        self.client.get("/")
    
    @task(2)
    def dashboard(self):
        self.client.get("/dashboard")
EOF

# اجرای تست با 1000 کاربر
locust -f locustfile.py --host=https://panel.yourdomain.com --users 1000 --spawn-rate 10
```

---

## <a name="monitoring"></a>6. مانیتورینگ و Alerting

### گام 1: راه‌اندازی Prometheus
```bash
docker-compose -f docker-compose.production.yml up -d prometheus
```

دسترسی: http://<SERVER_IP>:9090

### گام 2: راه‌اندازی Grafana
```bash
docker-compose -f docker-compose.production.yml up -d grafana
```

دسترسی: http://<SERVER_IP>:3000
- Username: admin
- Password: admin (تغییر دهید!)

### گام 3: Import داشبورد
1. ورود به Grafana
2. Configuration → Data Sources → Add Prometheus
3. URL: http://prometheus:9090
4. Import داشبورد از فایل `monitoring/dashboards/system_overview.json`

### گام 4: تنظیم Telegram Alerting
```bash
nano config/alerting.py
```

```python
TELEGRAM_ALERT_BOT_TOKEN = "<YOUR_BOT_TOKEN>"
TELEGRAM_ALERT_CHAT_ID = "<YOUR_CHAT_ID>"

ALERT_RULES = {
    'cpu_high': {'threshold': 80, 'duration': 300},
    'memory_high': {'threshold': 85, 'duration': 300},
    'disk_full': {'threshold': 90, 'duration': 60},
    'db_connections_high': {'threshold': 80, 'duration': 120}
}
```

---

## <a name="backup"></a>7. Backup و Recovery

### گام 1: Backup خودکار دیتابیس
```bash
sudo nano /etc/cron.daily/candidate-backup
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/candidate"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U candidate_user candidate_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Files backup
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /opt/candidate/uploads

# Keep last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
sudo chmod +x /etc/cron.daily/candidate-backup
```

### گام 2: Backup به سرور خارجی
```bash
# نصب rclone برای backup به cloud
curl https://rclone.org/install.sh | sudo bash

# پیکربندی (مثال: Google Drive)
rclone config

# Sync روزانه
sudo nano /etc/cron.daily/candidate-cloud-backup
```

```bash
#!/bin/bash
rclone sync /opt/backups/candidate remote:candidate-backups --transfers 4
```

### گام 3: Recovery از Backup
```bash
# بازیابی دیتابیس
gunzip -c /opt/backups/candidate/db_YYYYMMDD_HHMMSS.sql.gz | psql -U candidate_user candidate_db

# بازیابی فایل‌ها
tar -xzf /opt/backups/candidate/files_YYYYMMDD_HHMMSS.tar.gz -C /
```

---

## <a name="troubleshooting"></a>8. عیب‌یابی

### مشکل 1: سرویس Start نمی‌شود
```bash
# بررسی لاگ
sudo journalctl -u candidate-admin -f
sudo journalctl -u candidate-panel -f

# بررسی پورت‌ها
sudo netstat -tlnp | grep 5001
sudo netstat -tlnp | grep 5002

# تست دستی
source venv/bin/activate
gunicorn --bind 127.0.0.1:5001 admin_panel.app:app
```

### مشکل 2: خطای دیتابیس
```bash
# بررسی connection
psql -U candidate_user -d candidate_db -h localhost

# بررسی تعداد connection
SELECT count(*) FROM pg_stat_activity;

# Kill connection‌های معلق
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE state = 'idle' AND state_change < now() - interval '10 minutes';
```

### مشکل 3: Redis Connection Error
```bash
# بررسی Redis
redis-cli ping

# بررسی memory
redis-cli info memory

# پاک کردن cache
redis-cli FLUSHDB
```

### مشکل 4: CPU/Memory بالا
```bash
# بررسی فرآیندها
top -c
htop

# بررسی Gunicorn workers
ps aux | grep gunicorn

# Restart سرویس
sudo systemctl restart candidate-admin
sudo systemctl restart candidate-panel
```

### مشکل 5: خطای SSL
```bash
# تمدید SSL
sudo certbot renew

# تست SSL
openssl s_client -connect admin.yourdomain.com:443
```

---

## چک‌لیست نهایی قبل از Go-Live

- [ ] تمام `.env.production` پر شده
- [ ] SSL نصب و تست شده
- [ ] Backup خودکار فعال شده
- [ ] Monitoring راه‌اندازی شده
- [ ] Load test انجام شده (1000+ concurrent users)
- [ ] Security headers تنظیم شده
- [ ] Rate limiting فعال شده
- [ ] Admin IP whitelist تنظیم شده
- [ ] Database replication (اگر multi-server)
- [ ] Firewall rules تنظیم شده
- [ ] Log rotation فعال شده
- [ ] تست Telegram notifications
- [ ] داکیومنت recovery procedures
- [ ] آموزش تیم پشتیبانی

---

## پشتیبانی

برای مشکلات فنی:
- Email: support@yourdomain.com
- Telegram: @YourSupportBot
- Documentation: https://docs.yourdomain.com
