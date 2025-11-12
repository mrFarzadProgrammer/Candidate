"""
Migration: Update VIP-related tables with new fields
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import db
from sqlalchemy import text

def migrate_monthly_top_citizens():
    """Recreate monthly_top_citizens with new fields"""
    
    # بررسی وجود جدول
    result = db.session.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='monthly_top_citizens'"
    ))
    exists = result.fetchone() is not None
    
    if exists:
        print("🗑️  حذف جدول قدیمی monthly_top_citizens...")
        db.session.execute(text("DROP TABLE monthly_top_citizens"))
        db.session.commit()
    
    # ساخت جدول جدید
    print("✨ ساخت جدول جدید با فیلدهای کامل...")
    
    create_sql = """
    CREATE TABLE monthly_top_citizens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id INTEGER NOT NULL,
        citizen_telegram_id BIGINT NOT NULL,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        rank INTEGER NOT NULL,
        total_score INTEGER DEFAULT 0,
        contributions_count INTEGER DEFAULT 0,
        upvotes_count INTEGER DEFAULT 0,
        comments_count INTEGER DEFAULT 0,
        vip_status VARCHAR(20) DEFAULT 'gold',
        awarded_at TIMESTAMP,
        created_at TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES candidates(id),
        FOREIGN KEY (citizen_telegram_id) REFERENCES citizen_profiles(telegram_id)
    )
    """
    
    db.session.execute(text(create_sql))
    
    # ایجاد ایندکس‌ها
    db.session.execute(text(
        "CREATE INDEX ix_monthly_top_citizens_candidate_id ON monthly_top_citizens(candidate_id)"
    ))
    db.session.execute(text(
        "CREATE INDEX ix_monthly_top_citizens_year ON monthly_top_citizens(year)"
    ))
    db.session.execute(text(
        "CREATE INDEX ix_monthly_top_citizens_month ON monthly_top_citizens(month)"
    ))
    
    db.session.commit()
    print("✅ جدول monthly_top_citizens با موفقیت آپدیت شد")

if __name__ == '__main__':
    from candidate_panel.app import app
    
    with app.app_context():
        print("🔄 شروع migration جداول VIP...")
        migrate_monthly_top_citizens()
        print("✅ Migration کامل شد")
