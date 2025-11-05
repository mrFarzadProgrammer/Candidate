"""
Bot Runner - اجرای همه بات‌های فعال
این اسکریپت برای اجرا در کانتینر جداگانه طراحی شده
"""
import sys
import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import BotInstance
from bot_engine.bot_manager import BotManager
from config.settings import DATABASE_URI

print("🤖 Bot Runner Started...")
print(f"📡 Connecting to database: {DATABASE_URI}")

# اتصال به دیتابیس
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

# ایجاد مدیر بات
bot_manager = BotManager()

def start_all_active_bots():
    """راه‌اندازی تمام بات‌های فعال"""
    session = Session()
    try:
        active_bots = session.query(BotInstance).filter_by(is_active=True).all()
        
        if not active_bots:
            print("⚠️  هیچ بات فعالی یافت نشد")
            return
        
        print(f"✅ {len(active_bots)} بات فعال یافت شد")
        
        for bot in active_bots:
            try:
                print(f"🚀 راه‌اندازی بات @{bot.bot_username}...")
                bot_manager.start_bot(bot.id)
                time.sleep(2)  # فاصله بین راه‌اندازی بات‌ها
            except Exception as e:
                print(f"❌ خطا در راه‌اندازی بات {bot.id}: {str(e)}")
        
        print("\n✅ همه بات‌ها راه‌اندازی شدند")
        print("🔄 در حال انتظار...")
        
        # نگه داشتن پروسه زنده
        while True:
            time.sleep(60)
            print(f"💚 Bot Runner is running... Active bots: {len(bot_manager.get_active_bots())}")
            
    except KeyboardInterrupt:
        print("\n⏹️  در حال توقف بات‌ها...")
        session.close()
    except Exception as e:
        print(f"❌ خطا: {str(e)}")
        session.close()

if __name__ == '__main__':
    # انتظار برای آماده شدن دیتابیس
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # تست اتصال
            engine.connect()
            print("✅ اتصال به دیتابیس برقرار شد")
            break
        except Exception as e:
            retry_count += 1
            print(f"⏳ انتظار برای دیتابیس... ({retry_count}/{max_retries})")
            time.sleep(2)
    
    if retry_count >= max_retries:
        print("❌ خطا در اتصال به دیتابیس")
        sys.exit(1)
    
    # راه‌اندازی بات‌ها
    start_all_active_bots()
