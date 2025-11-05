"""
اسکریپت اصلی برای راه‌اندازی همه‌چیز
"""
import sys
import os
from multiprocessing import Process
import time
from threading import Thread

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def run_admin_panel():
    """راه‌اندازی پنل ادمین"""
    from admin_panel.app import app
    print("🔧 راه‌اندازی پنل ادمین در پورت 5000...")
    app.run(debug=False, port=5000, host='0.0.0.0', use_reloader=False)


def run_candidate_panel():
    """راه‌اندازی پنل نماینده"""
    from candidate_panel.app import app
    print("👤 راه‌اندازی پنل نماینده در پورت 5001...")
    app.run(debug=False, port=5001, host='0.0.0.0', use_reloader=False)


def run_all_bots():
    """راه‌اندازی تمام بات‌های فعال"""
    print("🤖 در حال راه‌اندازی بات‌ها...")
    time.sleep(3)  # صبر تا پنل‌ها بالا بیان
    
    from database.models import BotInstance
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from config.settings import DATABASE_URI
    from bot_engine.telegram_bot import run_bot
    
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        active_bots = session.query(BotInstance).filter_by(is_active=True).all()
        
        for bot in active_bots:
            print(f"🚀 راه‌اندازی بات @{bot.bot_username}...")
            bot_thread = Thread(target=run_bot, args=(bot.id,), daemon=True)
            bot_thread.start()
            time.sleep(1)
        
        if active_bots:
            print(f"✅ {len(active_bots)} بات راه‌اندازی شد")
        else:
            print("ℹ️  هیچ بات فعالی یافت نشد")
    
    finally:
        session.close()


def main():
    """راه‌اندازی همه سرویس‌ها"""
    print("="*60)
    print("🚀 سامانه مدیریت بات‌های انتخاباتی")
    print("="*60)
    
    # بررسی وجود دیتابیس
    if not os.path.exists('election_bot.db'):
        print("\n⚠️  دیتابیس یافت نشد. در حال مقداردهی اولیه...")
        from init_db import init_database
        init_database()
        time.sleep(2)
    
    print("\n📍 آدرس‌های دسترسی:")
    print("   پنل سوپر ادمین: http://localhost:5000")
    print("   پنل نماینده: http://localhost:5001")
    print("\n💡 برای توقف، Ctrl+C را فشار دهید")
    print("="*60)
    
    # راه‌اندازی پروسه‌ها
    admin_process = Process(target=run_admin_panel)
    candidate_process = Process(target=run_candidate_panel)
    bots_thread = Thread(target=run_all_bots, daemon=True)
    
    try:
        admin_process.start()
        time.sleep(1)  # فاصله برای جلوگیری از تداخل
        candidate_process.start()
        
        # راه‌اندازی بات‌ها
        bots_thread.start()
        
        # انتظار برای پروسه‌ها
        admin_process.join()
        candidate_process.join()
    
    except KeyboardInterrupt:
        print("\n\n⏹️  در حال توقف سرویس‌ها...")
        admin_process.terminate()
        candidate_process.terminate()
        admin_process.join()
        candidate_process.join()
        print("✅ سرویس‌ها متوقف شدند")


if __name__ == '__main__':
    main()
