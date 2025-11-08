#!/bin/bash
# Election Bot Deployment Script for VPS
# Server: 78.39.57.188

echo "🚀 Starting deployment of Election Bot Management System..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Update system
echo -e "${YELLOW}📦 Updating system packages...${NC}"
apt update && apt upgrade -y

# Step 2: Install Python 3.10+
echo -e "${YELLOW}🐍 Installing Python 3.10...${NC}"
apt install -y python3.10 python3.10-venv python3-pip

# Step 3: Install Git
echo -e "${YELLOW}📥 Installing Git...${NC}"
apt install -y git

# Step 4: Install Nginx
echo -e "${YELLOW}🌐 Installing Nginx...${NC}"
apt install -y nginx

# Step 5: Install Supervisor
echo -e "${YELLOW}📋 Installing Supervisor...${NC}"
apt install -y supervisor

# Step 6: Create application directory
echo -e "${YELLOW}📁 Creating application directory...${NC}"
mkdir -p /var/www/candidate
cd /var/www/candidate

# Step 7: Clone repository
echo -e "${YELLOW}📦 Cloning repository from GitHub...${NC}"
if [ -d ".git" ]; then
    echo "Repository exists, pulling latest changes..."
    git pull origin main
else
    git clone https://github.com/mrFarzadProgrammer/Candidate.git .
fi

# Step 8: Create Python virtual environment
echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
python3.10 -m venv venv
source venv/bin/activate

# Step 9: Install Python dependencies
echo -e "${YELLOW}📚 Installing Python packages...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Step 10: Create .env file
echo -e "${YELLOW}⚙️  Creating environment configuration...${NC}"
cat > .env << 'EOF'
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Database
DATABASE_URL=sqlite:///election_bot.db

# Server
HOST=0.0.0.0
PORT=5000
EOF

# Step 11: Initialize database
echo -e "${YELLOW}🗄️  Initializing database...${NC}"
python3 init_db.py

# Step 12: Create Gunicorn systemd service for Admin Panel
echo -e "${YELLOW}⚙️  Configuring Gunicorn service for Admin Panel...${NC}"
cat > /etc/systemd/system/election-admin.service << 'EOF'
[Unit]
Description=Election Bot Admin Panel (Gunicorn)
After=network.target

[Service]
Type=notify
User=root
Group=www-data
WorkingDirectory=/var/www/candidate
Environment="PATH=/var/www/candidate/venv/bin"
ExecStart=/var/www/candidate/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 admin_panel.app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Step 13: Create Gunicorn systemd service for Candidate Panel
echo -e "${YELLOW}⚙️  Configuring Gunicorn service for Candidate Panel...${NC}"
cat > /etc/systemd/system/election-candidate.service << 'EOF'
[Unit]
Description=Election Bot Candidate Panel (Gunicorn)
After=network.target

[Service]
Type=notify
User=root
Group=www-data
WorkingDirectory=/var/www/candidate
Environment="PATH=/var/www/candidate/venv/bin"
ExecStart=/var/www/candidate/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5001 candidate_panel.app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Step 14: Configure Nginx
echo -e "${YELLOW}🌐 Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/election-bot << 'EOF'
server {
    listen 80;
    server_name 78.39.57.188;
    client_max_body_size 20M;

    # Admin Panel
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Candidate Panel
    location /candidate {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Static files
    location /static {
        alias /var/www/candidate/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Uploads
    location /uploads {
        alias /var/www/candidate/uploads;
        expires 7d;
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/election-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Step 15: Set permissions
echo -e "${YELLOW}🔐 Setting permissions...${NC}"
chown -R root:www-data /var/www/candidate
chmod -R 755 /var/www/candidate
chmod -R 775 /var/www/candidate/uploads

# Step 16: Enable and start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
systemctl daemon-reload
systemctl enable election-admin
systemctl enable election-candidate
systemctl start election-admin
systemctl start election-candidate
systemctl restart nginx

# Step 17: Configure firewall
echo -e "${YELLOW}🔥 Configuring firewall...${NC}"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Step 18: Check service status
echo -e "${GREEN}✅ Checking service status...${NC}"
echo ""
echo "Admin Panel:"
systemctl status election-admin --no-pager | head -n 10
echo ""
echo "Candidate Panel:"
systemctl status election-candidate --no-pager | head -n 10
echo ""
echo "Nginx:"
systemctl status nginx --no-pager | head -n 5

# Final message
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📌 Access Information:${NC}"
echo -e "   Admin Panel:     ${GREEN}http://78.39.57.188/${NC}"
echo -e "   Candidate Panel: ${GREEN}http://78.39.57.188/candidate${NC}"
echo -e "   Username:        ${GREEN}admin${NC}"
echo -e "   Password:        ${GREEN}admin123${NC}"
echo ""
echo -e "${YELLOW}📝 Useful Commands:${NC}"
echo "   Check admin status:     systemctl status election-admin"
echo "   Check candidate status: systemctl status election-candidate"
echo "   View admin logs:        journalctl -u election-admin -f"
echo "   View candidate logs:    journalctl -u election-candidate -f"
echo "   Restart admin:          systemctl restart election-admin"
echo "   Restart candidate:      systemctl restart election-candidate"
echo "   Nginx logs:             tail -f /var/log/nginx/access.log"
echo ""
echo -e "${GREEN}🎉 Your Election Bot Management System is now live!${NC}"
echo ""
