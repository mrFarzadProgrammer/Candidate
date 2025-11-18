# -*- coding: utf-8 -*-
"""
Migration script for Gamification features
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin_panel.app import app, db
from sqlalchemy import text

def migrate():
    """اضافه کردن فیلدهای gamification به bot_users"""
    with app.app_context():
        try:
            # فیلدهای gamification در BotUser
            print("🔄 Adding gamification fields to bot_users table...")
            
            queries = [
                "ALTER TABLE bot_users ADD COLUMN total_points INTEGER DEFAULT 0",
                "ALTER TABLE bot_users ADD COLUMN level INTEGER DEFAULT 1",
                "ALTER TABLE bot_users ADD COLUMN streak_days INTEGER DEFAULT 0",
                "ALTER TABLE bot_users ADD COLUMN last_daily_login DATE"
            ]
            
            for query in queries:
                try:
                    db.session.execute(text(query))
                    db.session.commit()
                    print(f"✅ {query.split('ADD COLUMN')[1].split()[0]}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"⚠️  Column already exists: {query.split('ADD COLUMN')[1].split()[0]}")
                    else:
                        print(f"❌ Error: {e}")
            
            # ایجاد جدول Badge
            print("\n🔄 Creating Badge table...")
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS badges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    emoji VARCHAR(10),
                    icon_url VARCHAR(200),
                    condition_type VARCHAR(50),
                    condition_value INTEGER,
                    color VARCHAR(20),
                    rarity VARCHAR(20),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ Badge table created")
            
            # ایجاد جدول UserBadge
            print("🔄 Creating UserBadge table...")
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_badges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_user_id INTEGER NOT NULL,
                    badge_id INTEGER NOT NULL,
                    earned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_pinned BOOLEAN DEFAULT 0,
                    FOREIGN KEY (bot_user_id) REFERENCES bot_users(id),
                    FOREIGN KEY (badge_id) REFERENCES badges(id)
                )
            """))
            print("✅ UserBadge table created")
            
            # ایجاد جدول GamificationAction
            print("🔄 Creating GamificationAction table...")
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS gamification_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    points INTEGER DEFAULT 0,
                    is_repeatable BOOLEAN DEFAULT 1,
                    cooldown_minutes INTEGER DEFAULT 0,
                    max_per_day INTEGER,
                    counts_for_streak BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ GamificationAction table created")
            
            # ایجاد جدول UserPoints
            print("🔄 Creating UserPoints table...")
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_user_id INTEGER NOT NULL,
                    action_code VARCHAR(50) NOT NULL,
                    points INTEGER NOT NULL,
                    description TEXT,
                    reference_id INTEGER,
                    reference_type VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bot_user_id) REFERENCES bot_users(id)
                )
            """))
            print("✅ UserPoints table created")
            
            # ایجاد جدول Leaderboard
            print("🔄 Creating Leaderboard table...")
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS leaderboards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_instance_id INTEGER NOT NULL,
                    bot_user_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    rank INTEGER NOT NULL,
                    total_points INTEGER NOT NULL,
                    level INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bot_instance_id) REFERENCES bot_instances(id),
                    FOREIGN KEY (bot_user_id) REFERENCES bot_users(id)
                )
            """))
            print("✅ Leaderboard table created")
            
            db.session.commit()
            
            print("\n" + "="*50)
            print("✅ Migration completed successfully!")
            print("="*50)
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            db.session.rollback()

if __name__ == '__main__':
    migrate()
