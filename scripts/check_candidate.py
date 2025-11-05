"""
بررسی اطلاعات نماینده در دیتابیس
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import db, Candidate
from config.settings import DATABASE_URI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ایجاد اتصال به دیتابیس
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

print("🔍 بررسی نمایندگان در دیتابیس:")
print("=" * 60)

candidates = session.query(Candidate).all()

if not candidates:
    print("❌ هیچ نماینده‌ای در دیتابیس وجود ندارد!")
else:
    print(f"✅ تعداد نمایندگان: {len(candidates)}\n")
    
    for idx, candidate in enumerate(candidates, 1):
        print(f"\n📋 نماینده {idx}:")
        print(f"   ID: {candidate.id}")
        print(f"   نام کامل: {candidate.full_name}")
        print(f"   نام کاربری: {candidate.username}")
        print(f"   تلفن: {candidate.phone}")
        print(f"   رمز عبور (هش شده): {candidate.password[:50]}...")
        print(f"   تاریخ ثبت‌نام: {candidate.created_at}")
        print(f"   تعداد پلن‌ها: {len(candidate.plans)}")
        
        if candidate.plans:
            print("   پلن‌های فعال:")
            for plan in candidate.plans:
                print(f"      - {plan.name_fa} ({plan.code})")

print("\n" + "=" * 60)

session.close()
