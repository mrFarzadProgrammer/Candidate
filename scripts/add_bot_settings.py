# -*- coding: utf-8 -*-
"""
اضافه کردن فیلدهای تنظیمات بات به دیتابیس
"""
import sys
import os

# اضافه کردن مسیر پروژه
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.models import db, BotInstance
import config.settings as settings
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # اضافه کردن ستون‌های جدید
    from sqlalchemy import text
    
    columns_to_add = [
        ("bot_name", "VARCHAR(100)"),
        ("bot_about", "VARCHAR(120)"),
        ("bot_description", "TEXT"),
        ("bot_description_picture", "VARCHAR(200)"),
        ("bot_pic", "VARCHAR(200)"),
        ("bot_commands", "TEXT"),
        ("privacy_policy_url", "VARCHAR(500)")
    ]
    
    for column_name, column_type in columns_to_add:
        try:
            query = text(f"ALTER TABLE bot_instances ADD COLUMN {column_name} {column_type}")
            db.session.execute(query)
            db.session.commit()
            print(f"✅ ستون {column_name} با موفقیت اضافه شد")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"⚠️  ستون {column_name} از قبل موجود است")
                db.session.rollback()
            else:
                print(f"❌ خطا در اضافه کردن ستون {column_name}: {e}")
                db.session.rollback()
    
    print("\n✅ مایگریشن با موفقیت انجام شد!")
