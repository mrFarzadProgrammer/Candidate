"""
تنظیمات امنیتی پروژه
Security Configuration for Election Bot System
"""

import os
from datetime import timedelta

class SecurityConfig:
    """تنظیمات امنیتی سیستم"""
    
    # 1. SECRET KEYS - باید از environment بیاید
    SECRET_KEY = os.getenv('SECRET_KEY', 'CHANGE-THIS-IN-PRODUCTION')
    ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', 'CHANGE-THIS-TOO')
    
    # 2. SESSION SECURITY
    SESSION_COOKIE_SECURE = True  # فقط HTTPS
    SESSION_COOKIE_HTTPONLY = True  # جلوگیری از JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # محافظت در برابر CSRF
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # 2 ساعت
    SESSION_REFRESH_EACH_REQUEST = True
    
    # 3. CSRF PROTECTION
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # بدون محدودیت زمانی
    WTF_CSRF_SSL_STRICT = True
    
    # 4. PASSWORD POLICY
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    PASSWORD_HISTORY_COUNT = 5  # 5 رمز قبلی نشود
    PASSWORD_MAX_AGE_DAYS = 90  # هر 90 روز تغییر
    
    # 5. RATE LIMITING (جلوگیری از حملات)
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # محدودیت‌های مختلف
    RATE_LIMITS = {
        'login': '5 per minute',  # 5 تلاش ورود در دقیقه
        'register': '3 per hour',  # 3 ثبت‌نام در ساعت
        'api': '100 per minute',  # 100 درخواست API
        'broadcast': '10 per hour',  # 10 پیام همگانی در ساعت
        'admin': '200 per minute',  # ادمین بیشتر
    }
    
    # 6. FILE UPLOAD SECURITY
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {
        'image': {'png', 'jpg', 'jpeg', 'gif'},
        'document': {'pdf', 'doc', 'docx'},
        'audio': {'mp3', 'ogg', 'wav'}
    }
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    
    # 7. DATABASE SECURITY
    SQLALCHEMY_ECHO = False  # عدم نمایش query در production
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 8. CORS (برای API)
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://yourdomain.com').split(',')
    
    # 9. IP WHITELIST برای Admin Panel
    ADMIN_IP_WHITELIST = os.getenv('ADMIN_IP_WHITELIST', '').split(',')
    ENABLE_IP_WHITELIST = os.getenv('ENABLE_IP_WHITELIST', 'False') == 'True'
    
    # 10. TWO-FACTOR AUTHENTICATION
    ENABLE_2FA = os.getenv('ENABLE_2FA', 'True') == 'True'
    TOTP_ISSUER = 'ElectionBot'
    
    # 11. ENCRYPTION
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')  # برای encrypt کردن داده‌های حساس
    
    # 12. AUDIT LOGGING
    ENABLE_AUDIT_LOG = True
    AUDIT_LOG_EVENTS = [
        'login', 'logout', 'password_change', 
        'admin_action', 'data_export', 
        'payment', 'user_delete'
    ]
    
    # 13. BACKUP
    AUTO_BACKUP_ENABLED = True
    BACKUP_INTERVAL_HOURS = 6  # هر 6 ساعت
    BACKUP_RETENTION_DAYS = 30  # نگه‌داری 30 روز
    BACKUP_ENCRYPTION = True
    
    # 14. SECURITY HEADERS
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # 15. MONITORING
    ENABLE_INTRUSION_DETECTION = True
    FAILED_LOGIN_THRESHOLD = 5  # بعد از 5 بار قفل شود
    ACCOUNT_LOCKOUT_DURATION = 30  # 30 دقیقه قفل
    
    # 16. DATA RETENTION
    DELETE_INACTIVE_USERS_AFTER_DAYS = 365
    ANONYMIZE_DATA_AFTER_ELECTION = True


class DevelopmentSecurityConfig(SecurityConfig):
    """تنظیمات برای Development"""
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_SSL_STRICT = False
    ENABLE_IP_WHITELIST = False


class ProductionSecurityConfig(SecurityConfig):
    """تنظیمات برای Production - سخت‌گیرانه‌تر"""
    # همه چیز از environment بیاید
    if not os.getenv('SECRET_KEY'):
        raise ValueError("SECRET_KEY must be set in production!")
    
    if not os.getenv('ENCRYPTION_KEY'):
        raise ValueError("ENCRYPTION_KEY must be set in production!")
    
    # فعال‌سازی همه محافظت‌ها
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True
    ENABLE_2FA = True
    ENABLE_IP_WHITELIST = True
    ENABLE_AUDIT_LOG = True
    AUTO_BACKUP_ENABLED = True
