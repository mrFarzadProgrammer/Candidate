# -*- coding: utf-8 -*-
"""
مایگریشن: اضافه کردن سیستم پلن‌بندی پیشرفته
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.models import db, Plan, PlanPurchase, ConsultationRequest
import config.settings as settings
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    from sqlalchemy import text
    
    print("=" * 60)
    print("🚀 شروع مایگریشن سیستم پلن‌بندی")
    print("=" * 60)
    
    # 1. اضافه کردن ستون‌های جدید به جدول plans
    print("\n📋 مرحله 1: به‌روزرسانی جدول plans...")
    
    plan_columns = [
        ("max_messages", "INTEGER DEFAULT -1"),
        ("max_programs", "INTEGER DEFAULT -1"),
        ("max_headquarters", "INTEGER DEFAULT -1"),
        ("max_bot_users", "INTEGER DEFAULT -1"),
        ("has_ai", "BOOLEAN DEFAULT 0"),
        ("ai_message_classification", "BOOLEAN DEFAULT 0"),
        ("ai_sentiment_analysis", "BOOLEAN DEFAULT 0"),
        ("ai_auto_reply", "BOOLEAN DEFAULT 0"),
        ("ai_content_generation", "BOOLEAN DEFAULT 0"),
        ("ai_smart_chatbot", "BOOLEAN DEFAULT 0"),
        ("can_mass_message", "BOOLEAN DEFAULT 0"),
        ("max_mass_message_per_day", "INTEGER DEFAULT 0"),
        ("has_analytics", "BOOLEAN DEFAULT 0"),
        ("has_advanced_analytics", "BOOLEAN DEFAULT 0"),
        ("priority_support", "BOOLEAN DEFAULT 0"),
        ("display_order", "INTEGER DEFAULT 0"),
        ("badge_color", "VARCHAR(20) DEFAULT 'primary'"),
        ("is_popular", "BOOLEAN DEFAULT 0")
    ]
    
    for column_name, column_type in plan_columns:
        try:
            query = text(f"ALTER TABLE plans ADD COLUMN {column_name} {column_type}")
            db.session.execute(query)
            db.session.commit()
            print(f"  ✅ ستون {column_name} اضافه شد")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"  ⚠️  ستون {column_name} از قبل موجود است")
                db.session.rollback()
            else:
                print(f"  ❌ خطا در {column_name}: {e}")
                db.session.rollback()
    
    # 2. ایجاد جدول plan_purchases
    print("\n📋 مرحله 2: ایجاد جدول plan_purchases...")
    try:
        db.create_all()
        print("  ✅ جدول plan_purchases ایجاد شد")
    except Exception as e:
        print(f"  ⚠️  جدول احتمالاً از قبل وجود دارد: {e}")
    
    # 3. ایجاد جدول consultation_requests
    print("\n📋 مرحله 3: ایجاد جدول consultation_requests...")
    try:
        db.create_all()
        print("  ✅ جدول consultation_requests ایجاد شد")
    except Exception as e:
        print(f"  ⚠️  جدول احتمالاً از قبل وجود دارد: {e}")
    
    # 4. ایجاد پلن‌های پیش‌فرض
    print("\n📋 مرحله 4: ایجاد پلن‌های پیش‌فرض...")
    
    default_plans = [
        {
            'name': 'پایه',
            'code': 'BASIC',
            'description': 'پلن ورودی برای شروع کمپین انتخاباتی',
            'price': 500000,  # 500 هزار تومان
            'duration_days': 30,
            'max_messages': 100,
            'max_programs': 5,
            'max_headquarters': 3,
            'max_bot_users': -1,
            'has_ai': False,
            'can_mass_message': False,
            'has_analytics': True,
            'has_advanced_analytics': False,
            'priority_support': False,
            'display_order': 1,
            'badge_color': 'primary',
            'is_popular': False,
            'is_active': True
        },
        {
            'name': 'حرفه‌ای',
            'code': 'PROFESSIONAL',
            'description': 'برای کاندیداهای جدی با امکانات پیشرفته',
            'price': 2000000,  # 2 میلیون تومان
            'duration_days': 30,
            'max_messages': -1,  # نامحدود
            'max_programs': -1,
            'max_headquarters': -1,
            'max_bot_users': -1,
            'has_ai': True,
            'ai_message_classification': True,
            'ai_sentiment_analysis': True,
            'ai_auto_reply': True,
            'can_mass_message': True,
            'max_mass_message_per_day': 1000,
            'has_analytics': True,
            'has_advanced_analytics': True,
            'priority_support': False,
            'display_order': 2,
            'badge_color': 'success',
            'is_popular': True,
            'is_active': True
        },
        {
            'name': 'طلایی',
            'code': 'GOLD',
            'description': 'پلن کامل با تمام امکانات هوش مصنوعی',
            'price': 5000000,  # 5 میلیون تومان
            'duration_days': 30,
            'max_messages': -1,
            'max_programs': -1,
            'max_headquarters': -1,
            'max_bot_users': -1,
            'has_ai': True,
            'ai_message_classification': True,
            'ai_sentiment_analysis': True,
            'ai_auto_reply': True,
            'ai_content_generation': True,
            'ai_smart_chatbot': True,
            'can_mass_message': True,
            'max_mass_message_per_day': -1,
            'has_analytics': True,
            'has_advanced_analytics': True,
            'priority_support': True,
            'display_order': 3,
            'badge_color': 'warning',
            'is_popular': False,
            'is_active': True
        }
    ]
    
    for plan_data in default_plans:
        existing = Plan.query.filter_by(code=plan_data['code']).first()
        if not existing:
            plan = Plan(**plan_data)
            db.session.add(plan)
            print(f"  ✅ پلن {plan_data['name']} ایجاد شد")
        else:
            # به‌روزرسانی پلن موجود
            for key, value in plan_data.items():
                setattr(existing, key, value)
            print(f"  ✅ پلن {plan_data['name']} به‌روزرسانی شد")
    
    db.session.commit()
    
    print("\n" + "=" * 60)
    print("✅ مایگریشن با موفقیت انجام شد!")
    print("=" * 60)
    print("\n📊 آماده برای:")
    print("  - مدیریت پلن‌ها در پنل ادمین")
    print("  - خرید و ارتقای پلن در پنل کاندیدا")
    print("  - سیستم محدودیت‌ها و کنترل دسترسی")
    print("  - درخواست مشاوره و تماس")
    print("\n")
