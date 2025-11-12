# -*- coding: utf-8 -*-
"""
Add Database Indexes
افزودن Index به کالم‌های پرجستجو برای افزایش Performance
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.models import db
from config.settings import DATABASE_URI
from flask import Flask


def create_indexes():
    """
    Create database indexes for high-traffic queries
    """
    print("📊 Creating Database Indexes...")
    print("="*60)
    
    # Get database connection
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    with app.app_context():
        # Create indexes using raw SQL
        indexes = [
            # Candidates - جستجو بر اساس username و is_active
            ("idx_candidates_username", "CREATE INDEX IF NOT EXISTS idx_candidates_username ON candidates(username)"),
            ("idx_candidates_active", "CREATE INDEX IF NOT EXISTS idx_candidates_active ON candidates(is_active)"),
            ("idx_candidates_province", "CREATE INDEX IF NOT EXISTS idx_candidates_province ON candidates(province, city)"),
            
            # Messages - جستجو بر اساس candidate_id و created_at
            ("idx_messages_candidate", "CREATE INDEX IF NOT EXISTS idx_messages_candidate ON messages(candidate_id)"),
            ("idx_messages_created", "CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at DESC)"),
            ("idx_messages_candidate_created", "CREATE INDEX IF NOT EXISTS idx_messages_candidate_created ON messages(candidate_id, created_at DESC)"),
            ("idx_messages_is_read", "CREATE INDEX IF NOT EXISTS idx_messages_is_read ON messages(is_read, candidate_id)"),
            
            # Bot Users - جستجو بر اساس candidate_id و telegram_id
            ("idx_bot_users_candidate", "CREATE INDEX IF NOT EXISTS idx_bot_users_candidate ON bot_users(candidate_id)"),
            ("idx_bot_users_telegram", "CREATE INDEX IF NOT EXISTS idx_bot_users_telegram ON bot_users(telegram_id)"),
            ("idx_bot_users_candidate_telegram", "CREATE INDEX IF NOT EXISTS idx_bot_users_candidate_telegram ON bot_users(candidate_id, telegram_id)"),
            
            # Programs - جستجو بر اساس candidate_id
            ("idx_programs_candidate", "CREATE INDEX IF NOT EXISTS idx_programs_candidate ON programs(candidate_id)"),
            
            # Analytics - جستجو بر اساس candidate_id و date
            ("idx_analytics_candidate", "CREATE INDEX IF NOT EXISTS idx_analytics_candidate ON analytics(candidate_id)"),
            ("idx_analytics_date", "CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics(date DESC)"),
            ("idx_analytics_candidate_date", "CREATE INDEX IF NOT EXISTS idx_analytics_candidate_date ON analytics(candidate_id, date DESC)"),
            
            # Subscriptions - جستجو بر اساس candidate_id و is_active
            ("idx_subscriptions_candidate", "CREATE INDEX IF NOT EXISTS idx_subscriptions_candidate ON subscriptions(candidate_id)"),
            ("idx_subscriptions_active", "CREATE INDEX IF NOT EXISTS idx_subscriptions_active ON subscriptions(is_active)"),
            ("idx_subscriptions_expires", "CREATE INDEX IF NOT EXISTS idx_subscriptions_expires ON subscriptions(expires_at)"),
            
            # Bot Instances - جستجو بر اساس candidate_id
            ("idx_bot_instances_candidate", "CREATE INDEX IF NOT EXISTS idx_bot_instances_candidate ON bot_instances(candidate_id)"),
            ("idx_bot_instances_active", "CREATE INDEX IF NOT EXISTS idx_bot_instances_active ON bot_instances(is_active)"),
            
            # Headquarters - جستجو بر اساس candidate_id
            ("idx_headquarters_candidate", "CREATE INDEX IF NOT EXISTS idx_headquarters_candidate ON headquarters(candidate_id)"),
            
            # Resumes - جستجو بر اساس candidate_id
            ("idx_resumes_candidate", "CREATE INDEX IF NOT EXISTS idx_resumes_candidate ON resumes(candidate_id)"),
            
            # Slogans - جستجو بر اساس candidate_id
            ("idx_slogans_candidate", "CREATE INDEX IF NOT EXISTS idx_slogans_candidate ON slogans(candidate_id)"),
        ]
        
        created_count = 0
        failed_count = 0
        
        for index_name, sql in indexes:
            try:
                db.session.execute(db.text(sql))
                print(f"  ✅ {index_name}")
                created_count += 1
            except Exception as e:
                print(f"  ❌ {index_name}: {str(e)}")
                failed_count += 1
        
        # Commit changes
        try:
            db.session.commit()
            print()
            print("="*60)
            print(f"✅ Created {created_count} indexes")
            if failed_count > 0:
                print(f"⚠️  Failed {failed_count} indexes")
            print("="*60)
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Failed to commit: {e}")


if __name__ == '__main__':
    create_indexes()
