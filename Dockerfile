# Dockerfile برای اجرای پروژه
FROM python:3.10-slim

# نصب وابستگی‌های سیستمی
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# تنظیم دایرکتوری کاری
WORKDIR /app

# کپی فایل‌های پروژه
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ایجاد پوشه uploads
RUN mkdir -p /app/uploads

# پورت‌های پنل‌ها
EXPOSE 5000 5001

# اجرای برنامه
CMD ["python", "main.py"]
