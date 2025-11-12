"""
اسکریپت اضافه کردن/بروزرسانی پلن‌ها
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import db, Plan, Candidate
from config.settings import DATABASE_URI, DEFAULT_PLANS
from flask import Flask


def update_plans():
    """بروزرسانی پلن‌ها"""
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        print("🔄 در حال بروزرسانی پلن‌ها...")
        
        # حذف پلن‌های قدیمی
        old_plans = Plan.query.all()
        for plan in old_plans:
            db.session.delete(plan)
        db.session.commit()
        print(f"  🗑️ {len(old_plans)} پلن قدیمی حذف شد")
        
        # اضافه کردن پلن‌های جدید
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
        print(f"  ✅ {len(DEFAULT_PLANS)} پلن جدید اضافه شد")
        
        # نمایش لیست پلن‌ها
        print("\n📋 لیست پلن‌های جدید:")
        for plan in Plan.query.all():
            price_str = "رایگان" if plan.price == 0 else f"{plan.price:,} تومان"
            print(f"   {plan.name}")
            print(f"      💰 قیمت: {price_str}")
            print(f"      ⏱️ مدت: {plan.duration_days} روز")
            print(f"      📝 {plan.description[:80]}...")
            print()
        
        # اختصاص پلن پایه به همه نمایندگان
        print("🎁 در حال اختصاص پلن پایه استارت به نمایندگان...")
        base_plan = Plan.query.filter_by(code='START').first()
        
        if base_plan:
            candidates = Candidate.query.all()
            updated = 0
            
            for candidate in candidates:
                # پاک کردن پلن‌های قبلی
                candidate.plans.clear()
                # افزودن پلن پایه
                candidate.plans.append(base_plan)
                updated += 1
                print(f"  ✅ پلن پایه به {candidate.full_name} اختصاص داده شد")
            
            db.session.commit()
            print(f"\n✅ پلن پایه به {updated} نماینده اختصاص داده شد")
        else:
            print("  ⚠️ پلن پایه START یافت نشد!")
        
        print("\n🎉 تمام تغییرات با موفقیت اعمال شد!")


if __name__ == '__main__':
    update_plans()
