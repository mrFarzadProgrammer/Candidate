#!/bin/bash

# اسکریپت دیپلوی کامل پروژه روی سرور لینوکس
# Election Bot Management System

set -e  # توقف در صورت خطا

echo "=========================================="
echo "🚀 شروع دیپلوی پروژه انتخابات"
echo "=========================================="

# رنگ‌ها برای output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# متغیرها
PROJECT_DIR="/root/candidate"
PYTHON_VERSION="3.10"

echo -e "${BLUE}📦 مرحله 1: آپدیت سیستم${NC}"
apt-get update
apt-get upgrade -y

echo -e "${BLUE}📦 مرحله 2: نصب Python و ابزارهای لازم${NC}"
apt-get install -y python3.10 python3.10-venv python3-pip git nginx supervisor
apt-get install -y build-essential libssl-dev libffi-dev python3-dev

echo -e "${BLUE}📦 مرحله 3: کلون یا آپدیت پروژه${NC}"
if [ -d "$PROJECT_DIR" ]; then
    echo "پروژه وجود دارد، در حال آپدیت..."
    cd $PROJECT_DIR
    git pull origin main
else
    echo "در حال کلون پروژه..."
    git clone https://github.com/mrFarzadProgrammer/Candidate.git $PROJECT_DIR
    cd $PROJECT_DIR
fi

echo -e "${BLUE}📦 مرحله 4: ایجاد Virtual Environment${NC}"
if [ ! -d "venv" ]; then
    python3.10 -m venv venv
fi
source venv/bin/activate

echo -e "${BLUE}📦 مرحله 5: نصب Requirements${NC}"
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

echo -e "${BLUE}📦 مرحله 6: اجرای Migration‌ها${NC}"
python scripts/migrate_gamification.py
python scripts/migrate_ai_features.py

echo -e "${BLUE}📦 مرحله 7: پیکربندی Nginx${NC}"
cat > /etc/nginx/sites-available/candidate << 'EOF'
# Admin Panel
server {
    listen 80;
    server_name 78.39.57.188;

    location /admin/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /candidate/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /root/candidate/static/;
        expires 30d;
    }
}
EOF

# فعال کردن سایت
ln -sf /etc/nginx/sites-available/candidate /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo -e "${BLUE}📦 مرحله 8: پیکربندی Supervisor برای مدیریت Process‌ها${NC}"

# Admin Panel
cat > /etc/supervisor/conf.d/candidate-admin.conf << EOF
[program:candidate-admin]
directory=/root/candidate
command=/root/candidate/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 "admin_panel.app:app"
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/candidate-admin.err.log
stdout_logfile=/var/log/candidate-admin.out.log
environment=FLASK_APP="admin_panel/app.py"
EOF

# Candidate Panel
cat > /etc/supervisor/conf.d/candidate-panel.conf << EOF
[program:candidate-panel]
directory=/root/candidate
command=/root/candidate/venv/bin/gunicorn -w 4 -b 127.0.0.1:5001 "candidate_panel.app:app"
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/candidate-panel.err.log
stdout_logfile=/var/log/candidate-panel.out.log
environment=FLASK_APP="candidate_panel/app.py"
EOF

# Telegram Bot
cat > /etc/supervisor/conf.d/candidate-bot.conf << EOF
[program:candidate-bot]
directory=/root/candidate
command=/root/candidate/venv/bin/python run_bot_stable.py
user=root
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/candidate-bot.err.log
stdout_logfile=/var/log/candidate-bot.out.log
EOF

echo -e "${BLUE}📦 مرحله 9: راه‌اندازی Supervisor${NC}"
supervisorctl reread
supervisorctl update
supervisorctl restart all

echo -e "${BLUE}📦 مرحله 10: پیکربندی Firewall${NC}"
ufw allow 22
ufw allow 80
ufw allow 443
echo "y" | ufw enable

echo -e "${GREEN}=========================================="
echo "✅ دیپلوی با موفقیت انجام شد!"
echo "=========================================="
echo ""
echo "📍 آدرس‌های دسترسی:"
echo "   Admin Panel: http://78.39.57.188/admin/"
echo "   Candidate Panel: http://78.39.57.188/candidate/"
echo ""
echo "📊 مدیریت سرویس‌ها:"
echo "   supervisorctl status"
echo "   supervisorctl restart candidate-admin"
echo "   supervisorctl restart candidate-panel"
echo "   supervisorctl restart candidate-bot"
echo ""
echo "📝 مشاهده لاگ‌ها:"
echo "   tail -f /var/log/candidate-admin.out.log"
echo "   tail -f /var/log/candidate-panel.out.log"
echo "   tail -f /var/log/candidate-bot.out.log"
echo -e "${NC}"
