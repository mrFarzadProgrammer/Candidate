"""
اجرای پایدار بات تلگرام با مدیریت خطا
"""
import sys
import os
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import db, BotInstance, Candidate
from admin_panel.app import app
from bot_engine.telegram_bot import run_bot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """اجرای بات با restart خودکار در صورت خطا"""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            with app.app_context():
                # پیدا کردن بات فعال
                bot = BotInstance.query.filter_by(is_active=True).first()
                
                if not bot:
                    logger.error("❌ هیچ باتی فعال نیست!")
                    logger.info("از پنل ادمین بات را فعال کنید.")
                    return
                
                candidate = Candidate.query.get(bot.candidate_id)
                
                logger.info("="*50)
                logger.info(f"🤖 شروع بات برای: {candidate.full_name}")
                logger.info(f"📱 یوزرنیم بات: @{bot.bot_username}")
                logger.info(f"🆔 شناسه بات: {bot.id}")
                logger.info("="*50)
                
                # اجرای بات
                run_bot(bot.id)
                
        except KeyboardInterrupt:
            logger.info("\n⛔ بات توسط کاربر متوقف شد.")
            break
            
        except Exception as e:
            retry_count += 1
            logger.error(f"❌ خطا در اجرای بات (تلاش {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                wait_time = retry_count * 5
                logger.info(f"⏳ تلاش مجدد در {wait_time} ثانیه...")
                time.sleep(wait_time)
            else:
                logger.error("❌ تعداد تلاش‌های مجدد تمام شد. بات متوقف شد.")
                break


if __name__ == "__main__":
    main()
