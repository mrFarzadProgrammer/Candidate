"""
اسکریپت Migration برای ویژگی‌های جدید
- Benchmark و Ranking
- Trial و Referral
- VIP و Live Events
- احزاب و ائتلاف‌ها
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import db
from config.settings import DATABASE_URI
from flask import Flask

def create_app():
    """ایجاد اپلیکیشن Flask"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def migrate_database():
    """اجرای migration"""
    app = create_app()
    
    with app.app_context():
        print("🔄 شروع migration...")
        
        try:
            # ایجاد تمام جداول جدید
            db.create_all()
            
            print("✅ جداول جدید ایجاد شد:")
            print("   - marketplace_benchmarks (آمار بازار)")
            print("   - candidate_rankings (رتبه‌بندی نامزدها)")
            print("   - trial_periods (دوره‌های تریال)")
            print("   - referral_programs (برنامه معرفی)")
            print("   - referral_rewards (پاداش‌های معرفی)")
            print("   - monthly_top_citizens (شهروندان برتر ماه)")
            print("   - vip_interactions (تعاملات VIP)")
            print("   - live_events (رویدادهای زنده)")
            print("   - event_registrations (ثبت‌نام رویدادها)")
            print("   - political_parties (احزاب)")
            print("   - party_memberships (عضویت‌های حزب)")
            print("   - electoral_coalitions (ائتلاف‌ها)")
            print("   - coalition_memberships (عضویت‌های ائتلاف)")
            print("   - group_purchase_discounts (تخفیف گروهی)")
            
            print("\n✅ Migration با موفقیت انجام شد!")
            
        except Exception as e:
            print(f"❌ خطا در migration: {e}")
            return False
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Migration ویژگی‌های پیشرفته")
    print("=" * 60)
    
    success = migrate_database()
    
    if success:
        print("\n✅ تمام عملیات با موفقیت انجام شد")
    else:
        print("\n❌ خطا در اجرای migration")
        sys.exit(1)
