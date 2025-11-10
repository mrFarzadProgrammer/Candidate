"""
اجرای بات تلگرام برای نماینده
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import db, BotInstance, Candidate
from admin_panel.app import app
from bot_engine.telegram_bot import run_bot
import asyncio


def main():
    """اجرای بات برای اولین نماینده با بات فعال"""
    with app.app_context():
        # پیدا کردن بات فعال
        bot = BotInstance.query.filter_by(is_active=True).first()
        
        if not bot:
            print("❌ هیچ باتی فعال نیست!")
            print("از پنل ادمین بات را فعال کنید.")
            return
        
        candidate = Candidate.query.get(bot.candidate_id)
        
        print("="*50)
        print(f"🤖 شروع بات برای: {candidate.full_name}")
        print(f"📱 یوزرنیم بات: @{bot.bot_username}")
        print(f"🆔 شناسه بات: {bot.id}")
        print("="*50)
        
        # اجرای بات
        try:
            run_bot(bot.id)
        except KeyboardInterrupt:
            print("\n⛔ بات متوقف شد.")
        except Exception as e:
            print(f"❌ خطا در اجرای بات: {e}")


if __name__ == '__main__':
    main()
