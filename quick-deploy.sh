#!/bin/bash
# Quick Deployment Script - Run this on your VPS server

set -e

echo "🚀 Election Bot Quick Deployment"
echo "================================"

# Update & Install
echo "📦 Installing dependencies..."
apt update && apt install -y python3.10 python3.10-venv python3-pip git nginx supervisor

# Clone project
echo "📥 Cloning project..."
mkdir -p /var/www/candidate
cd /var/www/candidate
git clone https://github.com/mrFarzadProgrammer/Candidate.git . || (cd /var/www/candidate && git pull)

# Setup Python
echo "🐍 Setting up Python environment..."
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn

# Initialize database
echo "🗄️  Initializing database..."
python3 init_db.py

# Admin Panel Service
echo "⚙️  Creating Admin Panel service..."
cat > /etc/systemd/system/election-admin.service << 'EOFADMIN'
[Unit]
Description=Election Admin Panel
After=network.target
[Service]
Type=notify
User=root
WorkingDirectory=/var/www/candidate
Environment="PATH=/var/www/candidate/venv/bin"
ExecStart=/var/www/candidate/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 --timeout 120 admin_panel.app:app
Restart=always
[Install]
WantedBy=multi-user.target
EOFADMIN

# Candidate Panel Service
echo "⚙️  Creating Candidate Panel service..."
cat > /etc/systemd/system/election-candidate.service << 'EOFCAND'
[Unit]
Description=Election Candidate Panel
After=network.target
[Service]
Type=notify
User=root
WorkingDirectory=/var/www/candidate
Environment="PATH=/var/www/candidate/venv/bin"
ExecStart=/var/www/candidate/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5001 --timeout 120 candidate_panel.app:app
Restart=always
[Install]
WantedBy=multi-user.target
EOFCAND

# Nginx Config
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/election-bot << 'EOFNGINX'
server {
    listen 80;
    server_name _;
    client_max_body_size 20M;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    location /candidate {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /static {
        alias /var/www/candidate/static;
        expires 30d;
    }
}
EOFNGINX

ln -sf /etc/nginx/sites-available/election-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t

# Permissions
chmod -R 755 /var/www/candidate
mkdir -p /var/www/candidate/uploads
chmod -R 775 /var/www/candidate/uploads

# Start services
echo "🚀 Starting services..."
systemctl daemon-reload
systemctl enable election-admin election-candidate nginx
systemctl restart election-admin election-candidate nginx

# Status
echo ""
echo "✅ Deployment Complete!"
echo "======================="
echo "Admin Panel: http://78.39.57.188/"
echo "Username: admin"
echo "Password: admin123"
echo ""
echo "Check status: systemctl status election-admin"
echo "View logs: journalctl -u election-admin -f"
