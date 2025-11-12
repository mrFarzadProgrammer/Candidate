# -*- coding: utf-8 -*-
"""
تست‌های سیستم export داده
Data Export System Tests
"""

import pytest
import sys
import os
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from admin_panel.app import app, db
from database.models import Candidate, User, Message, Contribution
from data_export.export_system import DataExporter, ExportJob
from security.security_utils import hash_password


@pytest.fixture
def client():
    """فیکسچر test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def admin_user():
    """فیکسچر admin user"""
    with app.app_context():
        admin = Candidate(
            name='Admin Test',
            username='admin_test',
            password=hash_password('AdminPass123'),
            telegram_token='123:ABC',
            bot_username='admin_bot',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def test_data():
    """فیکسچر داده‌های تست"""
    with app.app_context():
        # ایجاد کاندیدها
        for i in range(5):
            candidate = Candidate(
                name=f'کاندید {i}',
                username=f'candidate_{i}',
                password=hash_password('Pass123'),
                telegram_token=f'123{i}:ABC',
                bot_username=f'bot_{i}'
            )
            db.session.add(candidate)
        
        db.session.commit()
        
        # ایجاد کاربران
        candidate_id = Candidate.query.first().id
        for i in range(10):
            user = User(
                telegram_id=1000000 + i,
                username=f'user_{i}',
                first_name=f'User {i}',
                candidate_id=candidate_id
            )
            db.session.add(user)
        
        db.session.commit()
        
        # ایجاد پیام‌ها
        user_id = User.query.first().id
        for i in range(20):
            message = Message(
                candidate_id=candidate_id,
                user_id=user_id,
                content=f'پیام تست {i}',
                message_type='text'
            )
            db.session.add(message)
        
        db.session.commit()


class TestExportEncryption:
    """تست‌های رمزنگاری export"""
    
    def test_export_file_is_encrypted(self, client, admin_user, test_data):
        """تست رمزنگاری فایل export"""
        exporter = DataExporter()
        
        # export کاندیدها
        export_path = exporter.export_candidates(
            admin_id=admin_user.id,
            encryption_password='SecurePassword123'
        )
        
        # چک کنیم فایل وجود داره
        assert os.path.exists(export_path)
        
        # چک کنیم محتوای فایل رمزنگاری شده (نباید JSON خام باشه)
        with open(export_path, 'rb') as f:
            content = f.read()
            # محتوای رمزنگاری شده نباید JSON قابل خواندن باشه
            assert not content.startswith(b'{')
            assert not content.startswith(b'[')
    
    def test_export_decryption_with_correct_password(self, client, admin_user, test_data):
        """تست رمزگشایی با پسورد صحیح"""
        exporter = DataExporter()
        password = 'SecurePassword123'
        
        # export کن
        export_path = exporter.export_candidates(
            admin_id=admin_user.id,
            encryption_password=password
        )
        
        # رمزگشایی کن
        decrypted_data = exporter.decrypt_export(export_path, password)
        
        # چک کنیم داده‌ها صحیح هستن
        assert decrypted_data is not None
        assert 'candidates' in decrypted_data
        assert len(decrypted_data['candidates']) == 5
    
    def test_export_decryption_fails_with_wrong_password(self, client, admin_user, test_data):
        """تست شکست رمزگشایی با پسورد اشتباه"""
        exporter = DataExporter()
        
        # export با پسورد
        export_path = exporter.export_candidates(
            admin_id=admin_user.id,
            encryption_password='CorrectPassword'
        )
        
        # تلاش برای رمزگشایی با پسورد اشتباه
        with pytest.raises(Exception):
            exporter.decrypt_export(export_path, 'WrongPassword')


class TestExportFormats:
    """تست‌های فرمت‌های مختلف export"""
    
    def test_export_candidates_json(self, client, admin_user, test_data):
        """تست export کاندیدها به JSON"""
        exporter = DataExporter()
        
        export_path = exporter.export_candidates(
            admin_id=admin_user.id,
            format='json',
            encryption_password='Pass123'
        )
        
        assert export_path.endswith('.json.enc')
        
        # رمزگشایی و بررسی ساختار
        data = exporter.decrypt_export(export_path, 'Pass123')
        assert 'candidates' in data
        assert 'export_date' in data
        assert 'exported_by' in data
    
    def test_export_users_csv(self, client, admin_user, test_data):
        """تست export کاربران به CSV"""
        exporter = DataExporter()
        candidate_id = Candidate.query.first().id
        
        export_path = exporter.export_users(
            admin_id=admin_user.id,
            candidate_id=candidate_id,
            format='csv',
            encryption_password='Pass123'
        )
        
        assert export_path.endswith('.csv.enc')
        
        # رمزگشایی
        data = exporter.decrypt_export(export_path, 'Pass123')
        assert data is not None
    
    def test_export_messages_excel(self, client, admin_user, test_data):
        """تست export پیام‌ها به Excel"""
        exporter = DataExporter()
        candidate_id = Candidate.query.first().id
        
        export_path = exporter.export_messages(
            admin_id=admin_user.id,
            candidate_id=candidate_id,
            format='excel',
            encryption_password='Pass123'
        )
        
        assert export_path.endswith('.xlsx.enc')


class TestDownloadLinks:
    """تست‌های لینک دانلود"""
    
    def test_download_link_generation(self, client, admin_user, test_data):
        """تست تولید لینک دانلود"""
        exporter = DataExporter()
        
        export_path = exporter.export_candidates(
            admin_id=admin_user.id,
            encryption_password='Pass123'
        )
        
        # ایجاد لینک دانلود
        download_link = exporter.create_download_link(export_path)
        
        assert download_link is not None
        assert '/download/' in download_link
        assert len(download_link) > 20  # شامل token امنیتی
    
    def test_download_link_expiry(self, client, admin_user, test_data):
        """تست منقضی شدن لینک دانلود"""
        exporter = DataExporter()
        
        export_path = exporter.export_candidates(
            admin_id=admin_user.id,
            encryption_password='Pass123'
        )
        
        # ایجاد لینک با expiry کوتاه (1 ثانیه)
        download_link = exporter.create_download_link(
            export_path,
            expiry_seconds=1
        )
        
        # صبر کن تا منقضی بشه
        time.sleep(2)
        
        # تلاش برای دانلود باید شکست بخوره
        response = client.get(download_link)
        assert response.status_code in [403, 404, 410]
    
    def test_download_link_single_use(self, client, admin_user, test_data):
        """تست یکبار مصرف بودن لینک"""
        exporter = DataExporter()
        
        export_path = exporter.export_candidates(
            admin_id=admin_user.id,
            encryption_password='Pass123'
        )
        
        download_link = exporter.create_download_link(
            export_path,
            single_use=True
        )
        
        # دانلود اول - موفق
        response1 = client.get(download_link)
        assert response1.status_code == 200
        
        # دانلود دوم - شکست
        response2 = client.get(download_link)
        assert response2.status_code in [403, 404, 410]


class TestExportCleanup:
    """تست‌های پاکسازی فایل‌های قدیمی"""
    
    def test_cleanup_old_exports(self, client, admin_user, test_data):
        """تست حذف فایل‌های قدیمی"""
        exporter = DataExporter()
        
        # ایجاد چند export
        paths = []
        for i in range(5):
            path = exporter.export_candidates(
                admin_id=admin_user.id,
                encryption_password='Pass123'
            )
            paths.append(path)
        
        # همه فایل‌ها موجود هستن
        for path in paths:
            assert os.path.exists(path)
        
        # پاکسازی فایل‌های قدیمی‌تر از 0 روز (همه)
        deleted_count = exporter.cleanup_old_exports(days_old=0)
        
        # حداقل چند فایل باید پاک شده باشه
        assert deleted_count > 0
    
    def test_cleanup_respects_age_limit(self, client, admin_user, test_data):
        """تست رعایت محدودیت سن فایل"""
        exporter = DataExporter()
        
        # ایجاد export جدید
        new_path = exporter.export_candidates(
            admin_id=admin_user.id,
            encryption_password='Pass123'
        )
        
        # پاکسازی فایل‌های قدیمی‌تر از 10 روز
        deleted_count = exporter.cleanup_old_exports(days_old=10)
        
        # فایل جدید نباید پاک بشه
        assert os.path.exists(new_path)


class TestExportPermissions:
    """تست‌های مجوزهای export"""
    
    def test_admin_can_export_all_candidates(self, client, admin_user, test_data):
        """تست export همه کاندیدها توسط admin"""
        exporter = DataExporter()
        
        export_path = exporter.export_candidates(
            admin_id=admin_user.id,
            encryption_password='Pass123'
        )
        
        data = exporter.decrypt_export(export_path, 'Pass123')
        
        # admin باید همه کاندیدها رو ببینه
        assert len(data['candidates']) == 5
    
    def test_candidate_can_only_export_own_data(self, client, test_data):
        """تست export فقط داده‌های خودی توسط کاندید"""
        with app.app_context():
            candidate = Candidate.query.filter_by(username='candidate_0').first()
            
            exporter = DataExporter()
            
            # تلاش برای export همه کاندیدها
            with pytest.raises(PermissionError):
                exporter.export_candidates(
                    admin_id=candidate.id,  # کاندید معمولی، نه admin
                    encryption_password='Pass123'
                )
    
    def test_candidate_can_export_own_users(self, client, test_data):
        """تست export کاربران خودی"""
        with app.app_context():
            candidate = Candidate.query.filter_by(username='candidate_0').first()
            
            exporter = DataExporter()
            
            export_path = exporter.export_users(
                admin_id=candidate.id,
                candidate_id=candidate.id,
                encryption_password='Pass123'
            )
            
            data = exporter.decrypt_export(export_path, 'Pass123')
            
            # باید فقط کاربران این کاندید باشه
            assert all(user['candidate_id'] == candidate.id 
                      for user in data['users'])


class TestExportAnalytics:
    """تست‌های export آنالیتیکس"""
    
    def test_export_includes_statistics(self, client, admin_user, test_data):
        """تست شامل شدن آمار در export"""
        exporter = DataExporter()
        candidate_id = Candidate.query.first().id
        
        export_path = exporter.export_analytics(
            admin_id=admin_user.id,
            candidate_id=candidate_id,
            encryption_password='Pass123'
        )
        
        data = exporter.decrypt_export(export_path, 'Pass123')
        
        # چک کنیم آمارها شامل هستن
        assert 'statistics' in data
        assert 'total_users' in data['statistics']
        assert 'total_messages' in data['statistics']
        assert 'user_growth' in data['statistics']
    
    def test_export_date_range_filter(self, client, admin_user, test_data):
        """تست فیلتر بازه زمانی"""
        exporter = DataExporter()
        candidate_id = Candidate.query.first().id
        
        # export آنالیتیکس 30 روز اخیر
        export_path = exporter.export_analytics(
            admin_id=admin_user.id,
            candidate_id=candidate_id,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            encryption_password='Pass123'
        )
        
        data = exporter.decrypt_export(export_path, 'Pass123')
        
        assert 'date_range' in data
        assert data['date_range']['days'] == 30


class TestExportJobs:
    """تست‌های job های export"""
    
    def test_export_job_creation(self, client, admin_user, test_data):
        """تست ایجاد job برای export بزرگ"""
        exporter = DataExporter()
        
        # ایجاد job
        job = exporter.create_export_job(
            admin_id=admin_user.id,
            export_type='candidates',
            encryption_password='Pass123'
        )
        
        assert job is not None
        assert job.status == 'pending'
        assert job.admin_id == admin_user.id
    
    def test_export_job_processing(self, client, admin_user, test_data):
        """تست پردازش job"""
        exporter = DataExporter()
        
        # ایجاد و پردازش job
        job = exporter.create_export_job(
            admin_id=admin_user.id,
            export_type='candidates',
            encryption_password='Pass123'
        )
        
        # پردازش job
        exporter.process_export_job(job.id)
        
        # بررسی وضعیت
        job = ExportJob.query.get(job.id)
        assert job.status in ['completed', 'processing']
        
        if job.status == 'completed':
            assert job.file_path is not None
            assert os.path.exists(job.file_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
