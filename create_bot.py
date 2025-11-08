#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
اسکریپت سریع ساخت بات
"""
import sys
from database.models import db, Candidate, BotInstance, Plan
from admin_panel.app import app
from werkzeug.security import generate_password_hash

def create_test_bot():
    """ساخت یک کاندیدا و بات تستی"""
    
    with app.app_context():
        print("\n" + "="*60)
        print("🤖 ساخت بات تستی")
        print("="*60)
        
        # چک کردن کاندیدا
        candidate = Candidate.query.filter_by(username='test_candidate').first()
        
        if not candidate:
            print("\n📝 ساخت کاندیدای تستی...")
            candidate = Candidate(
                username='test_candidate',
                password=generate_password_hash('123456'),
                full_name='کاندیدای تست',
                email='test@example.com',
                phone='09123456789'
            )
            db.session.add(candidate)
            db.session.commit()
            print(f"✅ کاندیدا ساخته شد: {candidate.full_name} (@{candidate.username})")
        else:
            print(f"✅ کاندیدا موجود است: {candidate.full_name} (@{candidate.username})")
        
        # حذف بات قبلی اگه وجود داره
        old_bot = BotInstance.query.filter_by(candidate_id=candidate.id).first()
        if old_bot:
            print(f"\n⚠️ بات قبلی پیدا شد: @{old_bot.username}")
            print("🗑️ در حال حذف بات قبلی...")
            db.session.delete(old_bot)
            db.session.commit()
        
        # دریافت توکن از کاربر
        print("\n" + "-"*60)
        print("📱 اکنون به تلگرام برو و این مراحل را انجام بده:")
        print("   1. جستجو کن: @BotFather")
        print("   2. بفرست: /newbot")
        print("   3. نام بات: Candidate Test Bot")
        print("   4. یوزرنیم: candidate_test_farzad_bot")
        print("   5. توکن را کپی کن")
        print("-"*60)
        
        token = input("\n🔑 توکن بات را اینجا بچسبان: ").strip()
        
        if not token or len(token) < 40:
            print("❌ توکن نامعتبر است!")
            return False
        
        # استخراج username از توکن (اگه ممکن باشه)
        bot_username = input("🤖 یوزرنیم بات (بدون @): ").strip()
        
        if not bot_username:
            bot_username = "test_bot"
        
        # ساخت بات
        print(f"\n📦 در حال ساخت بات...")
        new_bot = BotInstance(
            candidate_id=candidate.id,
            token=token,
            username=bot_username,
            is_active=True
        )
        db.session.add(new_bot)
        db.session.commit()
        
        print("\n" + "="*60)
        print("✅ بات با موفقیت ساخته شد!")
        print("="*60)
        print(f"   کاندیدا: {candidate.full_name}")
        print(f"   بات: @{new_bot.username}")
        print(f"   وضعیت: {'فعال' if new_bot.is_active else 'غیرفعال'}")
        print("="*60)
        
        print("\n🚀 حالا bot_runner.py را اجرا کن:")
        print("   python bot_runner.py")
        print("\n")
        
        return True

if __name__ == '__main__':
    try:
        create_test_bot()
    except KeyboardInterrupt:
        print("\n\n❌ لغو شد!")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
