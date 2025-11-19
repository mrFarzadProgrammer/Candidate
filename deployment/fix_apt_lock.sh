# دستورات برای حل مشکل apt lock

# روش 1: صبر کردن (بهترین روش)
# فقط 1-2 دقیقه صبر کن تا apt-get قبلی تمام شه

# روش 2: چک کردن پروسس
ps aux | grep apt

# روش 3: kill کردن پروسس (اگر گیر کرده)
sudo kill -9 9334

# روش 4: پاک کردن lock files (آخرین راه)
sudo rm /var/lib/dpkg/lock-frontend
sudo rm /var/lib/dpkg/lock
sudo dpkg --configure -a

# بعد دوباره اجرا کن:
./deployment/deploy_server.sh
