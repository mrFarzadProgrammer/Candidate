"""
ابزار مدیریت نمایندگان - برای حل مشکلات ورود
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import db, Candidate
from config.settings import DATABASE_URI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

# ایجاد اتصال به دیتابیس
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

def list_candidates():
    """لیست نمایندگان"""
    candidates = session.query(Candidate).all()
    
    if not candidates:
        print("❌ هیچ نماینده‌ای در دیتابیس وجود ندارد!")
        return []
    
    print(f"\n📋 لیست نمایندگان ({len(candidates)} نفر):")
    print("=" * 60)
    
    for idx, candidate in enumerate(candidates, 1):
        print(f"{idx}. {candidate.full_name}")
        print(f"   نام کاربری: {candidate.username}")
        print(f"   تلفن: {candidate.phone}")
        print(f"   تاریخ ثبت: {candidate.created_at.strftime('%Y-%m-%d %H:%M')}")
        print()
    
    return candidates

def reset_password(candidate_id, new_password):
    """ریست رمز عبور"""
    candidate = session.query(Candidate).get(candidate_id)
    
    if not candidate:
        print("❌ نماینده پیدا نشد!")
        return False
    
    candidate.password = generate_password_hash(new_password)
    session.commit()
    
    print(f"\n✅ رمز عبور تغییر یافت!")
    print(f"   نام کاربری: {candidate.username}")
    print(f"   رمز عبور جدید: {new_password}")
    
    return True

def test_login(username, password):
    """تست ورود"""
    candidate = session.query(Candidate).filter_by(username=username).first()
    
    if not candidate:
        print(f"❌ نماینده با نام کاربری '{username}' پیدا نشد!")
        return False
    
    print(f"🔐 هش رمز در دیتابیس: {candidate.password[:80]}...")
    result = check_password_hash(candidate.password, password)
    
    if result:
        print(f"✅ ورود موفق!")
        print(f"   نام کامل: {candidate.full_name}")
        print(f"   تلفن: {candidate.phone}")
        return True
    else:
        print(f"❌ رمز عبور نادرست است!")
        # تست رمزهای دیگر
        print(f"\n🧪 تست رمزهای احتمالی:")
        for test_pwd in ['123456', '1234', 'admin', 'password']:
            if check_password_hash(candidate.password, test_pwd):
                print(f"   ✅ رمز صحیح: {test_pwd}")
                return True
        return False

def main():
    print("🔧 ابزار مدیریت نمایندگان")
    print("=" * 60)
    
    while True:
        print("\nعملیات:")
        print("1. نمایش لیست نمایندگان")
        print("2. ریست رمز عبور")
        print("3. تست ورود")
        print("4. خروج")
        
        choice = input("\nانتخاب کنید (1-4): ").strip()
        
        if choice == '1':
            list_candidates()
        
        elif choice == '2':
            candidates = list_candidates()
            if candidates:
                try:
                    idx = int(input("\nشماره نماینده را وارد کنید: ")) - 1
                    if 0 <= idx < len(candidates):
                        new_password = input("رمز عبور جدید: ").strip()
                        if new_password:
                            reset_password(candidates[idx].id, new_password)
                        else:
                            print("❌ رمز عبور نمی‌تواند خالی باشد!")
                    else:
                        print("❌ شماره نامعتبر!")
                except ValueError:
                    print("❌ ورودی نامعتبر!")
        
        elif choice == '3':
            username = input("نام کاربری: ").strip()
            password = input("رمز عبور: ").strip()
            test_login(username, password)
        
        elif choice == '4':
            print("\n👋 خداحافظ!")
            break
        
        else:
            print("❌ انتخاب نامعتبر!")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 خداحافظ!")
    finally:
        session.close()
