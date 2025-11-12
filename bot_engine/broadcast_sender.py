"""
سیستم ارسال پیام انبوه به کاربران بات
"""
import sys
import os
import time
import logging
from datetime import datetime, timedelta
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import db, BroadcastMessage, BroadcastLog, BotUser, BotInstance
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config.settings import DATABASE_URI

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('broadcast_sender.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ایجاد engine و session
engine = create_engine(DATABASE_URI)
SessionFactory = sessionmaker(bind=engine)


class BroadcastSender:
    """کلاس مدیریت ارسال پیام‌های انبوه"""
    
    def __init__(self):
        self.sending = False
        self.delay_between_messages = 0.05  # 50ms تاخیر بین هر پیام (محدودیت تلگرام)
    
    def check_and_send_broadcasts(self):
        """چک کردن و ارسال پیام‌های انبوه"""
        if self.sending:
            logger.info("⏳ در حال ارسال پیام قبلی...")
            return
        
        session = SessionFactory()
        
        try:
            # یافتن پیام‌های آماده ارسال
            now = datetime.utcnow()
            
            # پیام‌های فوری (بدون زمان‌بندی)
            immediate_broadcasts = session.query(BroadcastMessage).filter(
                BroadcastMessage.status == 'pending',
                BroadcastMessage.scheduled_time.is_(None)
            ).all()
            
            # پیام‌های زمان‌بندی شده که وقتشون رسیده
            scheduled_broadcasts = session.query(BroadcastMessage).filter(
                BroadcastMessage.status == 'pending',
                BroadcastMessage.scheduled_time.isnot(None),
                BroadcastMessage.scheduled_time <= now
            ).all()
            
            all_broadcasts = immediate_broadcasts + scheduled_broadcasts
            
            if not all_broadcasts:
                return
            
            logger.info(f"📢 {len(all_broadcasts)} پیام انبوه برای ارسال یافت شد")
            
            for broadcast in all_broadcasts:
                self.send_broadcast(broadcast, session)
        
        except Exception as e:
            logger.error(f"❌ خطا در چک کردن پیام‌های انبوه: {str(e)}")
            session.rollback()
        
        finally:
            session.close()
    
    def send_broadcast(self, broadcast, session):
        """ارسال یک پیام انبوه به تمام کاربران"""
        try:
            self.sending = True
            
            # به‌روزرسانی وضعیت
            broadcast.status = 'sending'
            broadcast.started_at = datetime.utcnow()
            session.commit()
            
            logger.info(f"🚀 شروع ارسال broadcast #{broadcast.id}")
            
            # دریافت اطلاعات بات
            bot_instance = session.query(BotInstance).get(broadcast.bot_instance_id)
            
            if not bot_instance or not bot_instance.is_active:
                raise Exception(f"بات {broadcast.bot_instance_id} یافت نشد یا غیرفعال است")
            
            # دریافت لیست کاربران بر اساس فیلتر
            users = self.get_target_users(broadcast, session)
            
            broadcast.total_users = len(users)
            session.commit()
            
            logger.info(f"👥 تعداد کاربران هدف: {len(users)}")
            
            sent_count = 0
            failed_count = 0
            
            # ارسال به هر کاربر
            for user in users:
                try:
                    # ارسال پیام
                    success = self.send_to_user(
                        bot_token=bot_instance.bot_token,
                        telegram_id=user.telegram_id,
                        message_text=broadcast.message_text,
                        media_type=broadcast.media_type,
                        media_url=broadcast.media_url
                    )
                    
                    if success:
                        sent_count += 1
                        log_status = 'sent'
                        error_msg = None
                    else:
                        failed_count += 1
                        log_status = 'failed'
                        error_msg = 'Unknown error'
                
                except Exception as e:
                    failed_count += 1
                    log_status = 'failed'
                    error_msg = str(e)
                    logger.warning(f"⚠️ خطا در ارسال به {user.telegram_id}: {error_msg}")
                
                # ثبت لاگ
                log = BroadcastLog(
                    broadcast_id=broadcast.id,
                    user_telegram_id=user.telegram_id,
                    status=log_status,
                    error_message=error_msg,
                    sent_at=datetime.utcnow() if log_status == 'sent' else None
                )
                session.add(log)
                
                # به‌روزرسانی شمارنده‌ها
                broadcast.sent_count = sent_count
                broadcast.failed_count = failed_count
                session.commit()
                
                # تاخیر بین پیام‌ها (جلوگیری از محدودیت تلگرام)
                time.sleep(self.delay_between_messages)
            
            # تکمیل ارسال
            broadcast.status = 'completed'
            broadcast.completed_at = datetime.utcnow()
            session.commit()
            
            logger.info(f"✅ ارسال broadcast #{broadcast.id} تکمیل شد - موفق: {sent_count}, ناموفق: {failed_count}")
        
        except Exception as e:
            logger.error(f"❌ خطا در ارسال broadcast #{broadcast.id}: {str(e)}")
            broadcast.status = 'failed'
            session.commit()
        
        finally:
            self.sending = False
    
    def get_target_users(self, broadcast, session):
        """دریافت لیست کاربران هدف بر اساس فیلتر"""
        query = session.query(BotUser).filter_by(bot_instance_id=broadcast.bot_instance_id)
        
        if broadcast.target_filter == 'active':
            # کاربرانی که در 7 روز گذشته فعال بودند
            week_ago = datetime.utcnow() - timedelta(days=7)
            query = query.filter(BotUser.last_interaction >= week_ago)
        
        elif broadcast.target_filter == 'new':
            # کاربرانی که در 3 روز گذشته عضو شدند
            three_days_ago = datetime.utcnow() - timedelta(days=3)
            query = query.filter(BotUser.joined_at >= three_days_ago)
        
        # همه کاربران (all) - فیلتر پیش‌فرض
        return query.all()
    
    def send_to_user(self, bot_token, telegram_id, message_text, media_type=None, media_url=None):
        """ارسال پیام به یک کاربر"""
        try:
            base_url = f"https://api.telegram.org/bot{bot_token}"
            
            # ارسال متن ساده
            if not media_type or media_type == 'none':
                url = f"{base_url}/sendMessage"
                data = {
                    'chat_id': telegram_id,
                    'text': message_text,
                    'parse_mode': 'HTML'
                }
            
            # ارسال عکس
            elif media_type == 'photo':
                url = f"{base_url}/sendPhoto"
                data = {
                    'chat_id': telegram_id,
                    'photo': media_url,
                    'caption': message_text,
                    'parse_mode': 'HTML'
                }
            
            # ارسال ویدیو
            elif media_type == 'video':
                url = f"{base_url}/sendVideo"
                data = {
                    'chat_id': telegram_id,
                    'video': media_url,
                    'caption': message_text,
                    'parse_mode': 'HTML'
                }
            
            # ارسال فایل
            elif media_type == 'document':
                url = f"{base_url}/sendDocument"
                data = {
                    'chat_id': telegram_id,
                    'document': media_url,
                    'caption': message_text,
                    'parse_mode': 'HTML'
                }
            
            else:
                raise Exception(f"نوع رسانه نامعتبر: {media_type}")
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result['ok']
            else:
                return False
        
        except Exception as e:
            logger.error(f"❌ خطا در ارسال به {telegram_id}: {str(e)}")
            return False
    
    def get_broadcast_stats(self, broadcast_id, session):
        """دریافت آمار یک پیام انبوه"""
        broadcast = session.query(BroadcastMessage).get(broadcast_id)
        
        if not broadcast:
            return None
        
        stats = {
            'id': broadcast.id,
            'status': broadcast.status,
            'total_users': broadcast.total_users,
            'sent_count': broadcast.sent_count,
            'failed_count': broadcast.failed_count,
            'success_rate': (broadcast.sent_count / broadcast.total_users * 100) if broadcast.total_users > 0 else 0,
            'created_at': broadcast.created_at,
            'started_at': broadcast.started_at,
            'completed_at': broadcast.completed_at
        }
        
        return stats


# سینگلتون برای استفاده در کل برنامه
broadcast_sender = BroadcastSender()


def start_broadcast_scheduler():
    """راه‌اندازی scheduler برای ارسال خودکار"""
    import schedule
    
    logger.info("🚀 Broadcast Scheduler راه‌اندازی شد")
    
    # هر 30 ثانیه یک بار چک کن
    schedule.every(30).seconds.do(broadcast_sender.check_and_send_broadcasts)
    
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    start_broadcast_scheduler()
