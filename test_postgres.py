"""
تست اتصال به PostgreSQL و مقداردهی اولیه
"""
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Database URL برای PostgreSQL در Docker
DATABASE_URL = "postgresql://election_user:dev_password@localhost:5433/election_bot"

print("🔍 در حال تست اتصال به PostgreSQL...")
print(f"📡 URL: {DATABASE_URL}")

try:
    # ایجاد engine
    engine = create_engine(DATABASE_URL)
    
    # تست اتصال
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✅ اتصال موفق!")
        print(f"📊 PostgreSQL Version: {version[:50]}...")
        
        # تست ایجاد جدول
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100)
            );
        """))
        conn.commit()
        print("✅ جدول تست ایجاد شد!")
        
        # حذف جدول تست
        conn.execute(text("DROP TABLE IF EXISTS test_table;"))
        conn.commit()
        print("✅ جدول تست حذف شد!")
    
    print("\n🎉 PostgreSQL کاملاً آماده است!")
    print("\n📌 مراحل بعدی:")
    print("1. تغییر DATABASE_URI در config/settings.py")
    print(f"   DATABASE_URI = '{DATABASE_URL}'")
    print("2. اجرای: python init_db.py")
    print("3. راه‌اندازی سیستم: python main.py")
    print("\n🌐 دسترسی‌ها:")
    print("   • Adminer (مدیریت DB): http://localhost:8080")
    print("     - System: PostgreSQL")
    print("     - Server: election_db_dev")
    print("     - Username: election_user")
    print("     - Password: dev_password")
    print("     - Database: election_bot")

except OperationalError as e:
    print(f"❌ خطا در اتصال: {e}")
    print("\n💡 راهکارها:")
    print("1. مطمئن شوید Docker در حال اجراست")
    print("2. مطمئن شوید PostgreSQL کانتینر اجرا شده:")
    print("   docker-compose -f docker-compose.dev.yml ps")
    print("3. بررسی لاگ:")
    print("   docker-compose -f docker-compose.dev.yml logs postgres")
    sys.exit(1)

except Exception as e:
    print(f"❌ خطای غیرمنتظره: {e}")
    sys.exit(1)
