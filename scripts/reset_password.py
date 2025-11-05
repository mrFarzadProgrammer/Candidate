"""
ریست رمز عبور نماینده
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

print("🔧 ریست رمز عبور نماینده:")
print("=" * 60)

# دریافت نماینده
candidate = session.query(Candidate).filter_by(username='farzad_mohammadi').first()

if not candidate:
    print("❌ نماینده پیدا نشد!")
else:
    print(f"✅ نماینده پیدا شد: {candidate.full_name}")
    print(f"   نام کاربری: {candidate.username}")
    
    # رمز عبور جدید
    new_password = "123456"
    candidate.password = generate_password_hash(new_password)
    
    session.commit()
    
    print(f"\n✅ رمز عبور با موفقیت تغییر یافت!")
    print(f"   رمز عبور جدید: {new_password}")
    print(f"\n🔐 اطلاعات ورود:")
    print(f"   نام کاربری: {candidate.username}")
    print(f"   رمز عبور: {new_password}")
    print(f"\n📱 آدرس پنل نماینده: http://localhost:5001/login")

print("\n" + "=" * 60)

session.close()
