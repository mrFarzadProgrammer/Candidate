# -*- coding: utf-8 -*-
"""
Migration: اضافه کردن فیلدهای Trial و کنترل ادمین
"""
import sqlite3
import os

# مسیر دیتابیس
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'election_bot.db')
print(f"📂 مسیر دیتابیس: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔄 شروع Migration...")
    
    # اضافه کردن فیلدهای جدید به plan_purchases
    migrations = [
        ("is_trial", "INTEGER DEFAULT 0"),
        ("trial_used", "INTEGER DEFAULT 0"),
        ("custom_duration_days", "INTEGER"),
        ("admin_granted", "INTEGER DEFAULT 0"),
        ("admin_note", "TEXT"),
    ]
    
    for field_name, field_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE plan_purchases ADD COLUMN {field_name} {field_type}")
            print(f"✅ فیلد '{field_name}' اضافه شد")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"⏭️  فیلد '{field_name}' از قبل موجود است")
            else:
                print(f"❌ خطا در '{field_name}': {e}")
    
    # اضافه کردن فیلد has_used_trial به candidates
    try:
        cursor.execute("ALTER TABLE candidates ADD COLUMN has_used_trial INTEGER DEFAULT 0")
        print(f"✅ فیلد 'has_used_trial' به candidates اضافه شد")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"⏭️  فیلد 'has_used_trial' از قبل موجود است")
        else:
            print(f"❌ خطا: {e}")
    
    conn.commit()
    print("\n✨ Migration با موفقیت انجام شد!")
    
except Exception as e:
    print(f"❌ خطا: {e}")
    if conn:
        conn.rollback()
finally:
    if conn:
        conn.close()

print("\n📊 فیلدهای جدید:")
print("- is_trial: آیا این خرید یک Trial است؟")
print("- trial_used: آیا کاندیدا قبلاً Trial استفاده کرده؟")
print("- custom_duration_days: مدت دلخواه ادمین")
print("- admin_granted: آیا ادمین رایگان داده؟")
print("- admin_note: یادداشت ادمین")
print("- has_used_trial (Candidate): آیا کاندیدا Trial استفاده کرده؟")
