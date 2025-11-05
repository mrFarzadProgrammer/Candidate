"""
بررسی وضعیت بات نماینده
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import db, Candidate, BotInstance
from config.settings import DATABASE_URI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ایجاد اتصال به دیتابیس
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

print("🤖 بررسی وضعیت بات نمایندگان:")
print("=" * 60)

candidates = session.query(Candidate).all()

for candidate in candidates:
    print(f"\n📋 نماینده: {candidate.full_name}")
    print(f"   نام کاربری: {candidate.username}")
    
    if candidate.bot_instance:
        bot = candidate.bot_instance
        print(f"   ✅ بات وجود دارد:")
        print(f"      نام کاربری بات: @{bot.bot_username}")
        print(f"      توکن: {bot.bot_token[:20]}...")
        print(f"      وضعیت: {'فعال' if bot.is_active else 'غیرفعال'}")
    else:
        print(f"   ❌ بات راه‌اندازی نشده است")
        print(f"   💡 برای راه‌اندازی بات:")
        print(f"      1. وارد پنل ادمین شوید: http://localhost:5000")
        print(f"      2. از BotFather در تلگرام یک بات بسازید")
        print(f"      3. توکن بات را در پنل ادمین وارد کنید")

print("\n" + "=" * 60)

session.close()
