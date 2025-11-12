"""
اضافه کردن جداول مدیریت کانال/گروه تلگرام
"""
import sqlite3
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import DATABASE_URI

def add_channel_tables():
    """ایجاد جداول جدید برای مدیریت کانال/گروه"""
    
    # استخراج مسیر دیتابیس
    db_path = DATABASE_URI.replace('sqlite:///', '')
    
    print(f"📂 اتصال به دیتابیس: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # جدول BotChannel
        print("\n📋 ایجاد جدول bot_channels...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_instance_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            channel_id BIGINT NOT NULL,
            channel_username VARCHAR(100),
            channel_title VARCHAR(200) NOT NULL,
            channel_type VARCHAR(20) DEFAULT 'channel',
            is_active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            member_count INTEGER DEFAULT 0,
            connected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_post_at DATETIME,
            auto_post_enabled BOOLEAN DEFAULT 1,
            moderation_enabled BOOLEAN DEFAULT 0,
            FOREIGN KEY (bot_instance_id) REFERENCES bot_instances(id),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
        """)
        print("✅ جدول bot_channels ایجاد شد")
        
        # جدول ScheduledPost
        print("\n📋 ایجاد جدول scheduled_posts...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            media_type VARCHAR(20),
            media_url VARCHAR(500),
            scheduled_time DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'pending',
            sent_at DATETIME,
            message_id BIGINT,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            disable_notification BOOLEAN DEFAULT 0,
            pin_message BOOLEAN DEFAULT 0,
            FOREIGN KEY (channel_id) REFERENCES bot_channels(id),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
        """)
        print("✅ جدول scheduled_posts ایجاد شد")
        
        # جدول ChannelStats
        print("\n📋 ایجاد جدول channel_stats...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS channel_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            date DATE NOT NULL DEFAULT CURRENT_DATE,
            member_count INTEGER DEFAULT 0,
            new_members INTEGER DEFAULT 0,
            left_members INTEGER DEFAULT 0,
            posts_count INTEGER DEFAULT 0,
            total_views INTEGER DEFAULT 0,
            FOREIGN KEY (channel_id) REFERENCES bot_channels(id)
        )
        """)
        print("✅ جدول channel_stats ایجاد شد")
        
        # Index برای بهبود performance
        print("\n📋 ایجاد Index ها...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bot_channels_candidate ON bot_channels(candidate_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bot_channels_bot ON bot_channels(bot_instance_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_posts_channel ON scheduled_posts(channel_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_posts_status ON scheduled_posts(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_posts_time ON scheduled_posts(scheduled_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_stats_date ON channel_stats(date)")
        print("✅ Index ها ایجاد شدند")
        
        conn.commit()
        print("\n✅ تمام جداول با موفقیت ایجاد شدند!")
        
        # نمایش تعداد رکوردها
        cursor.execute("SELECT COUNT(*) FROM bot_channels")
        print(f"\n📊 تعداد کانال‌ها: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM scheduled_posts")
        print(f"📊 تعداد پست‌های زمان‌بندی: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM channel_stats")
        print(f"📊 تعداد آمار روزانه: {cursor.fetchone()[0]}")
        
    except sqlite3.Error as e:
        print(f"\n❌ خطا در ایجاد جداول: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Migration: اضافه کردن سیستم مدیریت کانال/گروه")
    print("=" * 60)
    
    if add_channel_tables():
        print("\n" + "=" * 60)
        print("✅ Migration با موفقیت انجام شد!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Migration با خطا مواجه شد!")
        print("=" * 60)
        sys.exit(1)
