#!/bin/bash
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'
echo -e "${BLUE}=== دیپلوی سیستم ===${NC}"
apt update && apt upgrade -y
apt install -y python3.10 python3.10-venv python3-pip git nginx ufw
mkdir -p /var/www/candidate
cd /var/www/candidate
if [ -d ".git" ]; then git pull origin main; else git clone https://github.com/mrFarzadProgrammer/Candidate.git .; fi
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
python3 scripts/init_db.py
cat > /etc/systemd/system/election-admin.service << 'SVCEOF'
[Unit]
Description=Election Admin
After=network.target
[Service]
Type=notify
User=root
WorkingDirectory=/var/www/candidate
Environment="PATH=/var/www/candidate/venv/bin"
ExecStart=/var/www/candidate/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 admin_panel.app:app
Restart=always
[Install]
WantedBy=multi-user.target
SVCEOF
cat > /etc/systemd/system/election-candidate.service << 'SVCEOF'
[Unit]
Description=Election Candidate
After=network.target
[Service]
Type=notify
User=root
WorkingDirectory=/var/www/candidate
Environment="PATH=/var/www/candidate/venv/bin"
ExecStart=/var/www/candidate/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5001 candidate_panel.app:app
Restart=always
[Install]
WantedBy=multi-user.target
SVCEOF
cat > /etc/systemd/system/election-bot.service << 'SVCEOF'
[Unit]
Description=Election Bot
After=network.target
[Service]
Type=simple
User=root
WorkingDirectory=/var/www/candidate
Environment="PATH=/var/www/candidate/venv/bin"
ExecStart=/var/www/candidate/venv/bin/python run_bot.py
Restart=always
[Install]
WantedBy=multi-user.target
SVCEOF
cat > /etc/nginx/sites-available/election << 'NGXEOF'
server {
    listen 80;
    server_name 78.39.57.188;
    client_max_body_size 20M;
    location /admin/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
    }
    location / {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
    }
    location /static { alias /var/www/candidate/static; }
    location /uploads { alias /var/www/candidate/uploads; }
}
NGXEOF
ln -sf /etc/nginx/sites-available/election /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl daemon-reload
systemctl enable election-admin election-candidate election-bot
systemctl restart election-admin election-candidate election-bot nginx
ufw allow 22/tcp
ufw allow 80/tcp
echo "y" | ufw enable
echo -e "${GREEN} دیپلوی موفق!${NC}"
echo -e "پنل ادمین: http://78.39.57.188/admin/"
echo -e "پنل نماینده: http://78.39.57.188/"
