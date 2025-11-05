"""
تست ورود نماینده
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import db, Candidate
from config.settings import DATABASE_URI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import check_password_hash

# ایجاد اتصال به دیتابیس
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

print("🔐 تست ورود نماینده:")
print("=" * 60)

# دریافت نماینده
candidate = session.query(Candidate).filter_by(username='farzad_mohammadi').first()

if not candidate:
    print("❌ نماینده پیدا نشد!")
else:
    print(f"✅ نماینده پیدا شد: {candidate.full_name}")
    print(f"   نام کاربری: {candidate.username}")
    
    # تست رمز عبور
    test_passwords = ['123456', '1234', 'admin', 'password', 'farzad123']
    
    print("\n🧪 تست رمزهای عبور مختلف:")
    for pwd in test_passwords:
        result = check_password_hash(candidate.password, pwd)
        status = "✅ صحیح" if result else "❌ نادرست"
        print(f"   {pwd:15} -> {status}")

print("\n" + "=" * 60)
print("\n💡 اگر هیچ‌کدام از رمزهای بالا صحیح نبودند،")
print("   رمزی که هنگام ساخت نماینده وارد کردید را امتحان کنید.")

session.close()
