# دستورات دیپلوی برای کپی و اجرا در سرور

## 1. اتصال به سرور
```bash
ssh root@78.39.57.188
# Password: xOqyF28i75
```

## 2. نصب Python و ابزارها
```bash
apt update && apt upgrade -y
apt install -y python3.10 python3.10-venv python3-pip git nginx supervisor ufw
```

## 3. کلون پروژه
```bash
mkdir -p /var/www/candidate
cd /var/www/candidate
git clone https://github.com/mrFarzadProgrammer/Candidate.git .
```

## 4. نصب وابستگی‌ها
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

## 5. مقداردهی اولیه دیتابیس
```bash
python3 init_db.py
```

## 6. ساخت سرویس Admin Panel
```bash
cat > /etc/systemd/system/election-admin.service << 'EOF'
[Unit]
Description=Election Bot Admin Panel
After=network.target

[Service]
Type=notify
User=root
Group=www-data
WorkingDirectory=/var/www/candidate
Environment="PATH=/var/www/candidate/venv/bin"
ExecStart=/var/www/candidate/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 admin_panel.app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

## 7. ساخت سرویس Candidate Panel
```bash
cat > /etc/systemd/system/election-candidate.service << 'EOF'
[Unit]
Description=Election Bot Candidate Panel
After=network.target

[Service]
Type=notify
User=root
Group=www-data
WorkingDirectory=/var/www/candidate
Environment="PATH=/var/www/candidate/venv/bin"
ExecStart=/var/www/candidate/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5001 candidate_panel.app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

## 8. تنظیم Nginx
```bash
cat > /etc/nginx/sites-available/election-bot << 'EOF'
server {
    listen 80;
    server_name 78.39.57.188;
    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_redirect off;
    }

    location /candidate {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_redirect off;
    }

    location /static {
        alias /var/www/candidate/static;
        expires 30d;
    }

    location /uploads {
        alias /var/www/candidate/uploads;
        expires 7d;
    }
}
EOF

ln -sf /etc/nginx/sites-available/election-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
```

## 9. تنظیم دسترسی‌ها
```bash
chown -R root:www-data /var/www/candidate
chmod -R 755 /var/www/candidate
chmod -R 775 /var/www/candidate/uploads
```

## 10. راه‌اندازی سرویس‌ها
```bash
systemctl daemon-reload
systemctl enable election-admin election-candidate
systemctl start election-admin election-candidate
systemctl restart nginx
```

## 11. تنظیم Firewall
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

## 12. بررسی وضعیت
```bash
systemctl status election-admin
systemctl status election-candidate
systemctl status nginx
```

## 13. مشاهده لاگ‌ها
```bash
journalctl -u election-admin -f
journalctl -u election-candidate -f
tail -f /var/log/nginx/access.log
```

## آدرس‌های دسترسی
- پنل ادمین: http://78.39.57.188/
- پنل نماینده: http://78.39.57.188/candidate
- نام کاربری: admin
- رمز عبور: admin123
