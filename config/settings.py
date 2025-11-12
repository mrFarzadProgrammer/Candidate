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
        'name': '🚀 استارت (Start)',
        'code': 'START',
        'description': 'پلن پایه رایگان - شامل: نمایش اطلاعات شخصی، رزومه، برنامه‌های انتخاباتی، شعارها، لیست دفاتر، آپلود تصاویر، ویس، تحصیلات، استان و شهر',
        'price': 0,
        'duration_days': 9999
    },
    {
        'name': '💬 ارتباط مردمی (Connect)',
        'code': 'CONNECT',
        'description': 'تعامل مستقیم با رأی‌دهندگان - دریافت و مدیریت پیام‌های مردم، پاسخگویی سریع، دسته‌بندی پیام‌ها',
        'price': 500000,
        'duration_days': 30
    },
    {
        'name': '📣 پیام‌رسان انبوه (Broadcast)',
        'code': 'BROADCAST',
        'description': 'کمپین پیام‌رسانی گسترده - ارسال پیام همزمان به هزاران نفر، زمان‌بندی ارسال، قالب‌های آماده پیام',
        'price': 1200000,
        'duration_days': 30
    },
    {
        'name': '📊 تحلیلگر داده (Analytics)',
        'code': 'ANALYTICS',
        'description': 'دید جامع آماری کمپین - نمودار بازدید، نرخ تعامل، آمار جغرافیایی، گزارش روزانه/هفتگی',
        'price': 800000,
        'duration_days': 30
    },
    {
        'name': '🗳️ نظرسنج هوشمند (Poll Master)',
        'code': 'POLL_MASTER',
        'description': 'سنجش افکار عمومی - ایجاد نظرسنجی چندگزینه‌ای، نمایش نتایج آنی، تحلیل آماری پاسخ‌ها',
        'price': 650000,
        'duration_days': 30
    },
    {
        'name': '🤖 دستیار هوشمند (AI Assistant)',
        'code': 'AI_ASSISTANT',
        'description': 'پاسخگوی 24 ساعته - پاسخ خودکار به سوالات متداول با هوش مصنوعی، یادگیری از تعاملات',
        'price': 1800000,
        'duration_days': 30
    },
    {
        'name': '📍 نقشه ستادها (Map Pro)',
        'code': 'MAP_PRO',
        'description': 'راهنمای جغرافیایی کامل - نمایش تمام دفاتر روی نقشه، مسیریابی، اطلاعات تماس، ساعت کاری',
        'price': 450000,
        'duration_days': 30
    },
    {
        'name': '🎨 برند ساز (Branding)',
        'code': 'BRANDING',
        'description': 'هویت بصری حرفه‌ای - طراحی لوگو، پوستر، بنر، اینفوگرافیک، محتوای شبکه‌های اجتماعی',
        'price': 2500000,
        'duration_days': 30
    },
    {
        'name': '👑 پکیج پیروزی (Victory Pack)',
        'code': 'VICTORY_PACK',
        'description': 'همه امکانات در یک بسته - تمام پلن‌های بالا + پشتیبانی اختصاصی + مشاوره کمپین انتخاباتی + گزارش‌دهی روزانه',
        'price': 5000000,
        'duration_days': 60
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
