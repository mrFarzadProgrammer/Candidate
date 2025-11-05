"""
اسکریپت مقداردهی اولیه دیتابیس
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import db, Admin, Plan
from config.settings import DATABASE_URI, DEFAULT_PLANS
from flask import Flask
from werkzeug.security import generate_password_hash


def init_database():
    """ایجاد جداول و داده‌های اولیه"""
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        print("🗄️  در حال ایجاد جداول...")
        db.create_all()
        print("✅ جداول با موفقیت ایجاد شدند")
        
        # ایجاد ادمین پیش‌فرض
        if not Admin.query.first():
            print("\n👤 در حال ایجاد ادمین پیش‌فرض...")
            admin = Admin(
                username='admin',
                password=generate_password_hash('admin123'),
                full_name='مدیر سیستم'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ ادمین ایجاد شد:")
            print("   نام کاربری: admin")
            print("   رمز عبور: admin123")
            print("   ⚠️  لطفاً رمز عبور را در محیط production تغییر دهید!")
        
        # ایجاد پلن‌های پیش‌فرض
        if not Plan.query.first():
            print("\n💼 در حال ایجاد پلن‌های پیش‌فرض...")
            for plan_data in DEFAULT_PLANS:
                plan = Plan(
                    name=plan_data['name'],
                    code=plan_data['code'],
                    description=plan_data['description'],
                    price=plan_data['price'],
                    duration_days=plan_data['duration_days']
                )
                db.session.add(plan)
            
            db.session.commit()
            print(f"✅ {len(DEFAULT_PLANS)} پلن ایجاد شد")
            
            print("\n📋 لیست پلن‌ها:")
            for plan in Plan.query.all():
                print(f"   • {plan.name} ({plan.code}) - {plan.price:,} تومان")
        
        print("\n✅ مقداردهی اولیه با موفقیت انجام شد!")
        print("\n🚀 برای راه‌اندازی سیستم:")
        print("   پنل ادمین: python admin_panel/app.py")
        print("   پنل نماینده: python candidate_panel/app.py")


if __name__ == '__main__':
    init_database()
