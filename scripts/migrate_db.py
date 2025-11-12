"""
اسکریپت مایگریشن دیتابیس
افزودن فیلدهای جدید به جدول candidates
"""
import sys
import os
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import db, Candidate, Plan
from config.settings import DATABASE_URI
from flask import Flask


def migrate_database():
    """اعمال تغییرات جدید به دیتابیس"""
    
    # استخراج مسیر فایل دیتابیس از URI
    db_path = DATABASE_URI.replace('sqlite:///', '')
    
    if not os.path.exists(db_path):
        print("❌ فایل دیتابیس یافت نشد. لطفاً ابتدا init_db.py را اجرا کنید.")
        return
    
    print("🔄 در حال اعمال تغییرات به دیتابیس...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # لیست فیلدهای جدید
    new_columns = [
        ('last_name', 'VARCHAR(100)'),
        ('education', 'VARCHAR(200)'),
        ('province', 'VARCHAR(50)'),
        ('voice_file', 'VARCHAR(200)'),
    ]
    
    # بررسی و اضافه کردن ستون‌های جدید به جدول candidates
    cursor.execute("PRAGMA table_info(candidates)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    for column_name, column_type in new_columns:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE candidates ADD COLUMN {column_name} {column_type}")
                print(f"  ✅ ستون {column_name} اضافه شد")
            except Exception as e:
                print(f"  ⚠️ خطا در افزودن ستون {column_name}: {e}")
        else:
            print(f"  ℹ️ ستون {column_name} از قبل وجود دارد")
    
    # ایجاد جدول candidate_images اگر وجود ندارد
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            image_path VARCHAR(200) NOT NULL,
            caption VARCHAR(500),
            'order' INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id)
        )
    """)
    print("  ✅ جدول candidate_images ایجاد/تأیید شد")
    
    conn.commit()
    conn.close()
    
    print("\n✅ مایگریشن با موفقیت انجام شد!")
    
    # حالا پلن پایه را به همه نمایندگان اختصاص می‌دهیم
    print("\n🎁 در حال اختصاص پلن پایه به نمایندگان...")
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        base_plan = Plan.query.filter_by(code='START').first()
        if not base_plan:
            print("  ⚠️ پلن پایه START یافت نشد. ابتدا init_db.py را اجرا کنید.")
            return
        
        candidates = Candidate.query.all()
        updated = 0
        
        for candidate in candidates:
            if base_plan not in candidate.plans:
                candidate.plans.append(base_plan)
                updated += 1
                print(f"  ✅ پلن پایه به {candidate.full_name} اختصاص داده شد")
            else:
                print(f"  ℹ️ {candidate.full_name} قبلاً پلن پایه دارد")
        
        db.session.commit()
        print(f"\n✅ پلن پایه به {updated} نماینده اختصاص داده شد")
    
    print("\n🎉 تمام تغییرات با موفقیت اعمال شد!")
    print("\n🚀 برای راه‌اندازی سیستم:")
    print("   پنل ادمین: python admin_panel/app.py")
    print("   پنل نماینده: python candidate_panel/app.py")


if __name__ == '__main__':
    migrate_database()
