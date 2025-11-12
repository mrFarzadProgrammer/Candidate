"""
Post Scheduler - زمان‌بندی و ارسال خودکار پست‌ها به کانال‌ها
"""
import schedule
import time
import logging
from datetime import datetime, timedelta
from threading import Thread
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import db, ScheduledPost, BotChannel, BotInstance
from config.settings import DATABASE_URI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('post_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)


class PostScheduler:
    """کلاس مدیریت زمان‌بندی و ارسال پست‌ها"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        logger.info("🚀 Post Scheduler initialized")
    
    def check_and_send_posts(self):
        """چک کردن و ارسال پست‌های سررسید شده"""
        session = Session()
        
        try:
            # پیدا کردن پست‌های pending که زمانشان رسیده
            now = datetime.utcnow()
            pending_posts = session.query(ScheduledPost).filter(
                ScheduledPost.status == 'pending',
                ScheduledPost.scheduled_time <= now
            ).all()
            
            if not pending_posts:
                logger.debug("📭 هیچ پست جدیدی برای ارسال نیست")
                return
            
            logger.info(f"📬 {len(pending_posts)} پست برای ارسال یافت شد")
            
            for post in pending_posts:
                try:
                    self.send_post(post, session)
                except Exception as e:
                    logger.error(f"❌ خطا در ارسال پست {post.id}: {str(e)}")
                    self.handle_failed_post(post, str(e), session)
            
            session.commit()
            
        except Exception as e:
            logger.error(f"❌ خطا در چک کردن پست‌ها: {str(e)}")
            session.rollback()
        finally:
            session.close()
    
    def send_post(self, post, session):
        """ارسال یک پست به کانال"""
        # دریافت اطلاعات کانال و بات
        channel = session.query(BotChannel).get(post.channel_id)
        
        if not channel or not channel.is_active:
            raise Exception(f"کانال {post.channel_id} یافت نشد یا غیرفعال است")
        
        bot_instance = session.query(BotInstance).get(channel.bot_instance_id)
        
        if not bot_instance or not bot_instance.is_active:
            raise Exception(f"بات {channel.bot_instance_id} یافت نشد یا غیرفعال است")
        
        # ارسال به تلگرام
        success = self.send_to_telegram(
            bot_token=bot_instance.bot_token,
            chat_id=channel.channel_id,
            content=post.content,
            media_type=post.media_type,
            media_url=post.media_url,
            disable_notification=post.disable_notification
        )
        
        if success:
            # به‌روزرسانی وضعیت پست
            post.status = 'sent'
            post.sent_at = datetime.utcnow()
            post.message_id = success  # ID پیام ارسال شده
            
            # به‌روزرسانی آخرین زمان پست کانال
            channel.last_post_at = datetime.utcnow()
            
            logger.info(f"✅ پست {post.id} با موفقیت به کانال {channel.channel_title} ارسال شد")
            
            # Pin اگر لازم باشد
            if post.pin_message and success:
                self.pin_message(bot_instance.bot_token, channel.channel_id, success)
        else:
            raise Exception("ارسال به تلگرام ناموفق بود")
    
    def send_to_telegram(self, bot_token, chat_id, content, media_type=None, 
                        media_url=None, disable_notification=False):
        """ارسال پست به تلگرام"""
        try:
            import requests
            
            base_url = f"https://api.telegram.org/bot{bot_token}"
            
            # ارسال متن ساده
            if not media_type or media_type == 'none':
                url = f"{base_url}/sendMessage"
                data = {
                    'chat_id': chat_id,
                    'text': content,
                    'disable_notification': disable_notification,
                    'parse_mode': 'HTML'
                }
                
            # ارسال عکس
            elif media_type == 'photo':
                url = f"{base_url}/sendPhoto"
                data = {
                    'chat_id': chat_id,
                    'photo': media_url,
                    'caption': content,
                    'disable_notification': disable_notification,
                    'parse_mode': 'HTML'
                }
            
            # ارسال ویدیو
            elif media_type == 'video':
                url = f"{base_url}/sendVideo"
                data = {
                    'chat_id': chat_id,
                    'video': media_url,
                    'caption': content,
                    'disable_notification': disable_notification,
                    'parse_mode': 'HTML'
                }
            
            # ارسال فایل
            elif media_type == 'document':
                url = f"{base_url}/sendDocument"
                data = {
                    'chat_id': chat_id,
                    'document': media_url,
                    'caption': content,
                    'disable_notification': disable_notification,
                    'parse_mode': 'HTML'
                }
            
            else:
                raise Exception(f"نوع رسانه نامعتبر: {media_type}")
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result['ok']:
                    message_id = result['result']['message_id']
                    logger.info(f"✅ پیام با موفقیت ارسال شد (message_id: {message_id})")
                    return message_id
                else:
                    raise Exception(f"خطای تلگرام: {result.get('description', 'Unknown error')}")
            else:
                raise Exception(f"HTTP Error {response.status_code}: {response.text}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ خطای شبکه در ارسال به تلگرام: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ خطا در ارسال به تلگرام: {str(e)}")
            raise
    
    def pin_message(self, bot_token, chat_id, message_id):
        """پین کردن پیام"""
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{bot_token}/pinChatMessage"
            data = {
                'chat_id': chat_id,
                'message_id': message_id,
                'disable_notification': True
            }
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"📌 پیام {message_id} پین شد")
            else:
                logger.warning(f"⚠️ خطا در پین کردن پیام: {response.text}")
        
        except Exception as e:
            logger.error(f"❌ خطا در پین کردن پیام: {str(e)}")
    
    def handle_failed_post(self, post, error_message, session):
        """مدیریت پست‌های ناموفق"""
        post.retry_count += 1
        post.error_message = error_message
        
        # بعد از 3 بار retry، وضعیت را failed می‌کنیم
        if post.retry_count >= 3:
            post.status = 'failed'
            logger.error(f"❌ پست {post.id} بعد از {post.retry_count} تلاش ناموفق ماند")
        else:
            # زمان بعدی را 5 دقیقه بعد تنظیم می‌کنیم
            post.scheduled_time = datetime.utcnow() + timedelta(minutes=5)
            logger.warning(f"⚠️ پست {post.id} برای retry {post.retry_count} زمان‌بندی شد")
        
        session.commit()
    
    def cleanup_old_posts(self):
        """پاک کردن پست‌های قدیمی (بیش از 30 روز)"""
        session = Session()
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            deleted = session.query(ScheduledPost).filter(
                ScheduledPost.status.in_(['sent', 'failed']),
                ScheduledPost.sent_at < cutoff_date
            ).delete()
            
            session.commit()
            
            if deleted > 0:
                logger.info(f"🗑️ {deleted} پست قدیمی پاک شد")
        
        except Exception as e:
            logger.error(f"❌ خطا در پاک کردن پست‌های قدیمی: {str(e)}")
            session.rollback()
        finally:
            session.close()
    
    def start(self):
        """شروع scheduler"""
        if self.running:
            logger.warning("⚠️ Scheduler قبلاً در حال اجراست")
            return
        
        self.running = True
        
        # Schedule jobs
        schedule.every(1).minutes.do(self.check_and_send_posts)
        schedule.every(1).days.do(self.cleanup_old_posts)
        
        logger.info("✅ Post Scheduler شروع شد")
        logger.info("⏰ بررسی پست‌ها هر 1 دقیقه")
        logger.info("🗑️ پاکسازی پست‌های قدیمی هر 1 روز")
        
        # اجرای scheduler در thread جداگانه
        self.thread = Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
    
    def _run_scheduler(self):
        """اجرای مداوم scheduler"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"❌ خطا در اجرای scheduler: {str(e)}")
                time.sleep(5)
    
    def stop(self):
        """توقف scheduler"""
        self.running = False
        logger.info("🛑 Post Scheduler متوقف شد")


# Instance سراسری
scheduler = PostScheduler()


def start_scheduler():
    """تابع راه‌اندازی scheduler"""
    scheduler.start()


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Post Scheduler - سیستم زمان‌بندی پست")
    print("=" * 60)
    print("")
    print("⏰ در حال اجرا...")
    print("📝 لاگ‌ها در post_scheduler.log ذخیره می‌شوند")
    print("")
    print("برای توقف: Ctrl+C")
    print("=" * 60)
    
    try:
        scheduler.start()
        
        # نگه داشتن برنامه
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n🛑 در حال توقف...")
        scheduler.stop()
        print("✅ Post Scheduler با موفقیت متوقف شد")
