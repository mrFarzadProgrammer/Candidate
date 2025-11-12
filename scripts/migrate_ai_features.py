# -*- coding: utf-8 -*-
"""
Migration: Add AI Features to Messages
=======================================
اضافه کردن فیلدهای AI به جدول messages
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.models import db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_add_ai_fields():
    """اضافه کردن فیلدهای AI به جدول messages"""
    
    migrations = [
        # Category fields
        """
        ALTER TABLE messages 
        ADD COLUMN category VARCHAR(50);
        """,
        """
        ALTER TABLE messages 
        ADD COLUMN category_fa VARCHAR(50);
        """,
        """
        ALTER TABLE messages 
        ADD COLUMN category_confidence FLOAT;
        """,
        """
        ALTER TABLE messages 
        ADD COLUMN category_priority VARCHAR(20);
        """,
        
        # Sentiment fields
        """
        ALTER TABLE messages 
        ADD COLUMN sentiment_score FLOAT;
        """,
        """
        ALTER TABLE messages 
        ADD COLUMN sentiment_label VARCHAR(20);
        """,
    ]
    
    try:
        for i, migration in enumerate(migrations, 1):
            try:
                db.session.execute(text(migration))
                logger.info(f"✅ Migration {i}/{len(migrations)} executed successfully")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    logger.warning(f"⚠️  Migration {i} skipped (column already exists)")
                else:
                    raise
        
        db.session.commit()
        logger.info("🎉 All migrations completed successfully!")
        
        # Create indexes for better performance
        create_indexes()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Migration failed: {e}")
        return False


def create_indexes():
    """ایجاد indexها برای بهبود performance"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_messages_category ON messages(category);",
        "CREATE INDEX IF NOT EXISTS idx_messages_priority ON messages(category_priority);",
        "CREATE INDEX IF NOT EXISTS idx_messages_sentiment ON messages(sentiment_label);",
        "CREATE INDEX IF NOT EXISTS idx_messages_candidate_category ON messages(candidate_id, category);",
    ]
    
    try:
        for index in indexes:
            db.session.execute(text(index))
        db.session.commit()
        logger.info("✅ Indexes created successfully")
    except Exception as e:
        logger.warning(f"⚠️  Index creation warning: {e}")


def rollback_ai_fields():
    """حذف فیلدهای AI (rollback)"""
    
    rollbacks = [
        "ALTER TABLE messages DROP COLUMN IF EXISTS category;",
        "ALTER TABLE messages DROP COLUMN IF EXISTS category_fa;",
        "ALTER TABLE messages DROP COLUMN IF EXISTS category_confidence;",
        "ALTER TABLE messages DROP COLUMN IF EXISTS category_priority;",
        "ALTER TABLE messages DROP COLUMN IF EXISTS sentiment_score;",
        "ALTER TABLE messages DROP COLUMN IF EXISTS sentiment_label;",
    ]
    
    try:
        for rollback in rollbacks:
            db.session.execute(text(rollback))
        db.session.commit()
        logger.info("✅ Rollback completed successfully")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Rollback failed: {e}")
        return False


if __name__ == "__main__":
    from flask import Flask
    from config.settings import DATABASE_URI
    
    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize db
    db.init_app(app)
    
    with app.app_context():
        import sys
        
        if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
            logger.info("🔄 Starting rollback...")
            rollback_ai_fields()
        else:
            logger.info("🚀 Starting migration...")
            migrate_add_ai_fields()
        
        logger.info("✅ Done!")
