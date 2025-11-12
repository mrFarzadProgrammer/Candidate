"""
Security Middleware & Utilities
ابزارهای امنیتی و middleware
"""

from functools import wraps
from flask import request, abort, session, current_app, jsonify
from utils.db_utils import safe_commit
from utils.validators import Validator, validate_form_data
import hashlib
import secrets
import pyotp
import bcrypt
from datetime import datetime, timedelta
import re
from bleach import clean
import logging

# Setup logging
security_logger = logging.getLogger('security')


# ============================================================
# 1. PASSWORD HASHING با bcrypt
# ============================================================

def hash_password(password):
    """
    Hash کردن رمز عبور با bcrypt
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password, hashed):
    """
    تایید رمز عبور
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        return False


def validate_password_strength(password):
    """
    بررسی قدرت رمز عبور
    
    Returns:
        tuple: (is_valid, error_message)
    """
    errors = []
    
    if len(password) < 12:
        errors.append('رمز عبور باید حداقل 12 کاراکتر باشد')
    
    if not re.search(r'[A-Z]', password):
        errors.append('رمز عبور باید حداقل یک حرف بزرگ داشته باشد')
    
    if not re.search(r'[a-z]', password):
        errors.append('رمز عبور باید حداقل یک حرف کوچک داشته باشد')
    
    if not re.search(r'[0-9]', password):
        errors.append('رمز عبور باید حداقل یک عدد داشته باشد')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('رمز عبور باید حداقل یک کاراکتر خاص داشته باشد')
    
    # بررسی رمزهای رایج
    common_passwords = ['password123', 'admin123', '12345678', 'qwerty123']
    if password.lower() in common_passwords:
        errors.append('این رمز عبور بسیار رایج است')
    
    return (len(errors) == 0, errors)


# ============================================================
# 2. INPUT SANITIZATION
# ============================================================

def sanitize_input(text, allow_html=False):
    """
    پاک‌سازی ورودی برای جلوگیری از XSS
    """
    if not text:
        return text
    
    if allow_html:
        # فقط تگ‌های امن
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li']
        return clean(text, tags=allowed_tags, strip=True)
    else:
        # هیچ HTML
        return clean(text, tags=[], strip=True)


def validate_phone(phone):
    """اعتبارسنجی شماره تلفن"""
    pattern = r'^09\d{9}$'
    return bool(re.match(pattern, phone))


def validate_email(email):
    """اعتبارسنجی ایمیل"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username):
    """اعتبارسنجی نام کاربری"""
    # فقط حروف، اعداد و _
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return bool(re.match(pattern, username))


# ============================================================
# 3. TWO-FACTOR AUTHENTICATION (2FA)
# ============================================================

def generate_2fa_secret():
    """ساخت secret برای 2FA"""
    return pyotp.random_base32()


def get_2fa_qr_code(username, secret):
    """
    دریافت QR Code برای 2FA
    
    Returns:
        str: URI برای QR Code
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=username,
        issuer_name='ElectionBot'
    )


def verify_2fa_token(secret, token):
    """تایید کد 2FA"""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)  # 30 ثانیه tolerance


# ============================================================
# 4. IP WHITELIST
# ============================================================

def check_ip_whitelist(whitelist):
    """
    بررسی IP در whitelist
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            
            if client_ip not in whitelist:
                security_logger.warning(f'Unauthorized IP access attempt: {client_ip}')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_ip_required(f):
    """
    Decorator برای محدود کردن دسترسی ادمین به IPهای مشخص
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from security.security_config import ProductionSecurityConfig
        
        if not ProductionSecurityConfig.ENABLE_IP_WHITELIST:
            return f(*args, **kwargs)
        
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        whitelist = ProductionSecurityConfig.ADMIN_IP_WHITELIST
        
        if whitelist and client_ip not in whitelist:
            security_logger.warning(f'Admin access denied for IP: {client_ip}')
            abort(403, 'دسترسی غیرمجاز')
        
        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# 5. RATE LIMITING
# ============================================================

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # در production باید redis باشد
)


# ============================================================
# 6. AUDIT LOGGING
# ============================================================

def log_security_event(event_type, user_id=None, details=None):
    """
    ثبت رویداد امنیتی
    """
    from database.models import db, AuditLog
    
    log_entry = AuditLog(
        event_type=event_type,
        user_id=user_id,
        ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
        user_agent=request.headers.get('User-Agent', ''),
        details=details,
        created_at=datetime.utcnow()
    )
    
    db.session.add(log_entry)
    safe_commit(db, "Database commit failed")
    
    security_logger.info(f'Security Event: {event_type} - User: {user_id} - IP: {log_entry.ip_address}')


# ============================================================
# 7. FAILED LOGIN TRACKING
# ============================================================

failed_login_attempts = {}  # در production باید Redis باشد

def track_failed_login(username):
    """ثبت تلاش ناموفق ورود"""
    key = f'failed_login:{username}'
    
    if key not in failed_login_attempts:
        failed_login_attempts[key] = {'count': 0, 'locked_until': None}
    
    failed_login_attempts[key]['count'] += 1
    
    if failed_login_attempts[key]['count'] >= 5:
        # قفل کردن برای 30 دقیقه
        failed_login_attempts[key]['locked_until'] = datetime.utcnow() + timedelta(minutes=30)
        security_logger.warning(f'Account locked due to failed attempts: {username}')
        return True  # locked
    
    return False


def is_account_locked(username):
    """بررسی قفل بودن اکانت"""
    key = f'failed_login:{username}'
    
    if key not in failed_login_attempts:
        return False
    
    locked_until = failed_login_attempts[key].get('locked_until')
    
    if locked_until and datetime.utcnow() < locked_until:
        return True
    
    # باز کردن قفل
    if locked_until and datetime.utcnow() >= locked_until:
        failed_login_attempts[key] = {'count': 0, 'locked_until': None}
    
    return False


def reset_failed_logins(username):
    """ریست کردن تلاش‌های ناموفق بعد از ورود موفق"""
    key = f'failed_login:{username}'
    if key in failed_login_attempts:
        del failed_login_attempts[key]


# ============================================================
# 8. CSRF TOKEN VALIDATION
# ============================================================

def generate_csrf_token():
    """ساخت CSRF Token"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def validate_csrf_token(token):
    """تایید CSRF Token"""
    return token == session.get('_csrf_token')


# ============================================================
# 9. SECURITY HEADERS
# ============================================================

def add_security_headers(response):
    """
    افزودن هدرهای امنیتی به response
    
    استفاده:
        app.after_request(add_security_headers)
    """
    from security.security_config import SecurityConfig
    
    for header, value in SecurityConfig.SECURITY_HEADERS.items():
        response.headers[header] = value
    
    return response


# ============================================================
# 10. FILE UPLOAD VALIDATION
# ============================================================

def allowed_file(filename, file_type='image'):
    """بررسی پسوند فایل"""
    from security.security_config import SecurityConfig
    
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    allowed = SecurityConfig.ALLOWED_EXTENSIONS.get(file_type, set())
    
    return ext in allowed


def validate_file_content(file_path, expected_type='image'):
    """
    بررسی محتوای واقعی فایل (نه فقط پسوند)
    جلوگیری از upload فایل‌های مخرب با پسوند تصویر
    """
    import magic  # python-magic
    
    mime = magic.from_file(file_path, mime=True)
    
    allowed_mimes = {
        'image': ['image/jpeg', 'image/png', 'image/gif'],
        'document': ['application/pdf', 'application/msword'],
        'audio': ['audio/mpeg', 'audio/ogg']
    }
    
    return mime in allowed_mimes.get(expected_type, [])


def sanitize_filename(filename):
    """پاک‌سازی نام فایل"""
    # حذف کاراکترهای خطرناک
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # محدود کردن طول
    filename = filename[:100]
    return filename


# ============================================================
# 11. DATA ENCRYPTION
# ============================================================

from cryptography.fernet import Fernet

def get_encryption_key():
    """دریافت کلید رمزنگاری از environment"""
    import os
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        raise ValueError("ENCRYPTION_KEY not set!")
    return key.encode()


def encrypt_data(data):
    """رمزنگاری داده"""
    f = Fernet(get_encryption_key())
    return f.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data):
    """رمزگشایی داده"""
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_data.encode()).decode()


# ============================================================
# 12. SESSION SECURITY
# ============================================================

def secure_session(user_id, role='candidate'):
    """
    ساخت session امن
    """
    session.permanent = True
    session['user_id'] = user_id
    session['role'] = role
    session['created_at'] = datetime.utcnow().isoformat()
    session['last_activity'] = datetime.utcnow().isoformat()
    
    # ساخت session fingerprint برای جلوگیری از session hijacking
    user_agent = request.headers.get('User-Agent', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    session['fingerprint'] = hashlib.sha256(f'{user_agent}{ip}'.encode()).hexdigest()


def validate_session():
    """
    اعتبارسنجی session
    """
    if 'user_id' not in session:
        return False
    
    # بررسی fingerprint
    user_agent = request.headers.get('User-Agent', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    current_fingerprint = hashlib.sha256(f'{user_agent}{ip}'.encode()).hexdigest()
    
    if session.get('fingerprint') != current_fingerprint:
        security_logger.warning(f'Session hijacking attempt detected for user {session.get("user_id")}')
        return False
    
    # بررسی timeout
    last_activity = datetime.fromisoformat(session.get('last_activity', ''))
    if datetime.utcnow() - last_activity > timedelta(hours=2):
        return False
    
    # بروزرسانی last_activity
    session['last_activity'] = datetime.utcnow().isoformat()
    
    return True


# ============================================================
# 13. API KEY AUTHENTICATION (برای APIهای عمومی)
# ============================================================

def generate_api_key():
    """ساخت API Key"""
    return secrets.token_urlsafe(32)


def validate_api_key(api_key):
    """تایید API Key"""
    from database.models import Candidate
    candidate = Candidate.query.filter_by(api_key=api_key).first()
    return candidate is not None


def require_api_key(f):
    """Decorator برای محافظت از API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key or not validate_api_key(api_key):
            return jsonify({'error': 'Invalid API Key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function
