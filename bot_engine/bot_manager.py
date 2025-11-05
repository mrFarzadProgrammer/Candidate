"""
مدیر بات‌ها - راه‌اندازی و مدیریت بات‌های تلگرام
"""
import sys
import os
from threading import Thread
from typing import Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import BotInstance


class BotManager:
    """مدیریت چند بات به‌صورت همزمان"""
    
    def __init__(self):
        self.active_bots: Dict[int, Thread] = {}
    
    def start_bot(self, bot_instance_id: int):
        """راه‌اندازی یک بات"""
        from bot_engine.telegram_bot import run_bot
        
        if bot_instance_id in self.active_bots:
            print(f"بات {bot_instance_id} قبلاً راه‌اندازی شده است")
            return
        
        # ایجاد thread جدید برای بات
        bot_thread = Thread(target=run_bot, args=(bot_instance_id,), daemon=True)
        bot_thread.start()
        
        self.active_bots[bot_instance_id] = bot_thread
        print(f"✅ بات {bot_instance_id} راه‌اندازی شد")
    
    def stop_bot(self, bot_instance_id: int):
        """توقف یک بات"""
        if bot_instance_id in self.active_bots:
            # TODO: پیاده‌سازی توقف صحیح بات
            del self.active_bots[bot_instance_id]
            print(f"⛔ بات {bot_instance_id} متوقف شد")
    
    def restart_bot(self, bot_instance_id: int):
        """ریستارت بات"""
        self.stop_bot(bot_instance_id)
        self.start_bot(bot_instance_id)
    
    def get_active_bots(self):
        """لیست بات‌های فعال"""
        return list(self.active_bots.keys())
