"""
تنظیمات پروژه
"""
import os
from pathlib import Path

# مسیر پروژه
BASE_DIR = Path(__file__).resolve().parent.parent

# تنظیمات دیتابیس
# اول DATABASE_URL رو چک می‌کنیم (استاندارد Heroku/Render/PythonAnywhere)
# بعد DATABASE_URI رو چک می‌کنیم (برای سازگاری با کدهای قدیمی)
# و در آخر SQLite به عنوان fallback برای Development
DATABASE_URI = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URI') or f'sqlite:///{BASE_DIR}/election_bot.db'

# کلیدهای امنیتی
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', 'admin-secret-key-change-in-production')
CANDIDATE_SECRET_KEY = os.getenv('CANDIDATE_SECRET_KEY', 'candidate-secret-key-change-in-production')

# مسیر آپلود فایل‌ها
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# تنظیمات بات تلگرام
BOT_WEBHOOK_MODE = os.getenv('BOT_WEBHOOK_MODE', 'False').lower() == 'true'
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')

# پلن‌های پیش‌فرض
DEFAULT_PLANS = [
    {
        'name': 'پایه (رایگان)',
        'code': 'FREE',
        'description': 'نمایش اطلاعات عمومی، رزومه، برنامه‌ها',
        'price': 0,
        'duration_days': 365
    },
    {
        'name': 'ارتباط مردمی',
        'code': 'PUBLIC_MESSAGING',
        'description': 'دریافت پیام از مردم',
        'price': 500000,
        'duration_days': 30
    },
    {
        'name': 'ارسال پیام انبوه',
        'code': 'MASS_MESSAGING',
        'description': 'ارسال پیام به همه کاربران بات',
        'price': 1000000,
        'duration_days': 30
    },
    {
        'name': 'آمار و تحلیل',
        'code': 'ANALYTICS',
        'description': 'مشاهده بازدید، تعامل، نمودارها',
        'price': 750000,
        'duration_days': 30
    },
    {
        'name': 'نظرسنجی',
        'code': 'SURVEY',
        'description': 'ایجاد و نمایش نظرسنجی',
        'price': 600000,
        'duration_days': 30
    },
    {
        'name': 'پاسخ‌گوی هوشمند',
        'code': 'AI_RESPONDER',
        'description': 'پاسخ خودکار به سوالات پرتکرار',
        'price': 1500000,
        'duration_days': 30
    },
    {
        'name': 'نقشه ستادها',
        'code': 'MAP',
        'description': 'نمایش آدرس‌ها روی نقشه',
        'price': 400000,
        'duration_days': 30
    },
    {
        'name': 'برندینگ',
        'code': 'BRANDING',
        'description': 'طراحی محتوا، شعار، پوستر',
        'price': 2000000,
        'duration_days': 30
    },
]

# تنظیمات لاگ
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'app.log'),
            'mode': 'a',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}
