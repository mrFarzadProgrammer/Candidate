#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Migration Script: Add Security & Audit Models + Gradual Release
================================================================

This script adds:
1. AuditLog - Security event logging
2. DataExportLog - Data export tracking
3. BetaTester - Beta testing program
4. SystemConfig - System configuration key-value store
5. DiscountCampaign - Discount campaigns
6. Plan model updates - Gradual release fields

Usage:
    python scripts/migrate_security_audit.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.models import db
from sqlalchemy import inspect, text
from admin_panel.app import app

def table_exists(table_name):
    """بررسی وجود جدول"""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

def column_exists(table_name, column_name):
    """بررسی وجود ستون در جدول"""
    inspector = inspect(db.engine)
    if not table_exists(table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_security_audit():
    """اعمال مایگریشن‌های امنیتی و audit"""
    
    with app.app_context():
        print("=" * 60)
        print("🔐 Security & Audit Migration")
        print("=" * 60)
        
        # ایجاد جداول جدید
        print("\n📊 Creating new tables...")
        
        tables_to_create = [
            ('audit_logs', 'AuditLog'),
            ('data_export_logs', 'DataExportLog'),
            ('beta_testers', 'BetaTester'),
            ('system_configs', 'SystemConfig'),
            ('discount_campaigns', 'DiscountCampaign')
        ]
        
        for table_name, model_name in tables_to_create:
            if table_exists(table_name):
                print(f"   ✓ Table '{table_name}' already exists")
            else:
                print(f"   + Creating table '{table_name}'...")
        
        # ایجاد تمام جداول
        db.create_all()
        print("   ✓ All tables created/verified")
        
        # اضافه کردن ستون‌های جدید به جدول plans
        print("\n📝 Updating 'plans' table with gradual release fields...")
        
        plan_columns = [
            ('is_available_for_purchase', 'BOOLEAN', 'False'),
            ('release_scheduled_at', 'DATETIME', 'NULL'),
            ('release_notes', 'TEXT', 'NULL'),
            ('enabled_at', 'DATETIME', 'NULL'),
            ('enabled_by_admin_id', 'INTEGER', 'NULL')
        ]
        
        for column_name, column_type, default_value in plan_columns:
            if column_exists('plans', column_name):
                print(f"   ✓ Column '{column_name}' already exists")
            else:
                print(f"   + Adding column '{column_name}'...")
                try:
                    if column_type == 'BOOLEAN':
                        db.session.execute(text(
                            f"ALTER TABLE plans ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
                        ))
                    elif default_value == 'NULL':
                        db.session.execute(text(
                            f"ALTER TABLE plans ADD COLUMN {column_name} {column_type}"
                        ))
                    else:
                        db.session.execute(text(
                            f"ALTER TABLE plans ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
                        ))
                    db.session.commit()
                    print(f"   ✓ Column '{column_name}' added successfully")
                except Exception as e:
                    print(f"   ⚠ Error adding column '{column_name}': {e}")
                    db.session.rollback()
        
        # اضافه کردن داده‌های پیش‌فرض به system_configs
        print("\n⚙️  Adding default system configurations...")
        
        from database.models import SystemConfig
        
        default_configs = [
            {
                'key': 'maintenance_mode',
                'value': 'false',
                'description': 'فعال/غیرفعال بودن حالت نگهداری'
            },
            {
                'key': 'max_login_attempts',
                'value': '5',
                'description': 'حداکثر تعداد تلاش ناموفق ورود'
            },
            {
                'key': 'lockout_duration_minutes',
                'value': '15',
                'description': 'مدت زمان قفل شدن حساب (دقیقه)'
            },
            {
                'key': 'session_timeout_hours',
                'value': '24',
                'description': 'مدت زمان اعتبار نشست (ساعت)'
            },
            {
                'key': 'max_upload_size_mb',
                'value': '10',
                'description': 'حداکثر حجم آپلود فایل (مگابایت)'
            },
            {
                'key': 'auto_export_enabled',
                'value': 'false',
                'description': 'فعال بودن export خودکار داده‌ها'
            },
            {
                'key': 'export_retention_days',
                'value': '7',
                'description': 'مدت نگهداری فایل‌های export (روز)'
            },
            {
                'key': 'rate_limit_per_minute',
                'value': '100',
                'description': 'محدودیت درخواست در دقیقه'
            },
            {
                'key': 'beta_testing_enabled',
                'value': 'false',
                'description': 'فعال بودن برنامه بتا تستر'
            },
            {
                'key': 'gradual_release_enabled',
                'value': 'true',
                'description': 'فعال بودن انتشار مرحله‌ای پلن‌ها'
            }
        ]
        
        for config in default_configs:
            existing = SystemConfig.query.filter_by(key=config['key']).first()
            if not existing:
                new_config = SystemConfig(**config)
                db.session.add(new_config)
                print(f"   + Added config: {config['key']}")
            else:
                print(f"   ✓ Config '{config['key']}' already exists")
        
        db.session.commit()
        
        # نمایش آمار جداول
        print("\n📊 Database Statistics:")
        print("=" * 60)
        
        from database.models import AuditLog, DataExportLog, BetaTester, SystemConfig, DiscountCampaign
        
        stats = {
            'audit_logs': AuditLog.query.count() if table_exists('audit_logs') else 0,
            'data_export_logs': DataExportLog.query.count() if table_exists('data_export_logs') else 0,
            'beta_testers': BetaTester.query.count() if table_exists('beta_testers') else 0,
            'system_configs': SystemConfig.query.count() if table_exists('system_configs') else 0,
            'discount_campaigns': DiscountCampaign.query.count() if table_exists('discount_campaigns') else 0
        }
        
        for table_name, count in stats.items():
            print(f"   {table_name}: {count} records")
        
        print("\n✅ Migration completed successfully!")
        print("=" * 60)

if __name__ == '__main__':
    try:
        migrate_security_audit()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
