"""
ایجاد نماینده تست سریع
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import db, Candidate
from config.settings import DATABASE_URI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

# ایجاد اتصال به دیتابیس
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

print("📝 ایجاد نماینده تست:")
print("=" * 60)

# بررسی اینکه نماینده وجود داره یا نه
existing = session.query(Candidate).filter_by(username='farzad_mohammadi').first()

if existing:
    print(f"⚠️  نماینده قبلاً وجود داشته، در حال بروزرسانی...")
    existing.password = generate_password_hash('123456')
    session.commit()
    print(f"✅ رمز عبور بروزرسانی شد")
else:
    # ایجاد نماینده جدید
    candidate = Candidate(
        username='farzad_mohammadi',
        password=generate_password_hash('123456'),
        full_name='فرزاد محمدی',
        phone='09213986332'
    )
    
    session.add(candidate)
    session.commit()
    print(f"✅ نماینده جدید ایجاد شد")

print(f"\n🔐 اطلاعات ورود:")
print(f"   نام کاربری: farzad_mohammadi")
print(f"   رمز عبور: 123456")
print(f"\n📱 آدرس پنل نماینده: http://localhost:5001/login")
print("=" * 60)

session.close()
