# -*- coding: utf-8 -*-
"""
تست‌های سیستم VIP شهروندان
VIP Citizens System Tests
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from candidate_panel.app import app, db
from database.models import (
    Candidate, User, VIPCitizen, VIPInteraction,
    VIPMeeting, MonthlyTopCitizens
)
from candidate_panel.vip_utils import VIPManager
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
def test_candidate():
    """فیکسچر کاندید تست"""
    with app.app_context():
        candidate = Candidate(
            name='کاندید تست',
            username='test_candidate',
            password=hash_password('Pass123'),
            telegram_token='123:ABC',
            bot_username='test_bot'
        )
        db.session.add(candidate)
        db.session.commit()
        return candidate


@pytest.fixture
def test_users(test_candidate):
    """فیکسچر کاربران تست"""
    with app.app_context():
        users = []
        for i in range(20):
            user = User(
                telegram_id=1000000 + i,
                username=f'user_{i}',
                first_name=f'User {i}',
                candidate_id=test_candidate.id
            )
            db.session.add(user)
            users.append(user)
        
        db.session.commit()
        return users


class TestVIPAward:
    """تست‌های اعطای VIP"""
    
    def test_award_vip_status(self, client, test_candidate, test_users):
        """تست اعطای وضعیت VIP"""
        manager = VIPManager()
        user = test_users[0]
        
        # اعطای VIP
        success = manager.award_vip_status(
            candidate_id=test_candidate.id,
            user_id=user.id,
            reason='مشارکت فعال',
            duration_months=3
        )
        
        assert success is True
        
        # بررسی وضعیت
        vip = VIPCitizen.query.filter_by(
            candidate_id=test_candidate.id,
            user_id=user.id
        ).first()
        
        assert vip is not None
        assert vip.is_active is True
    
    def test_vip_expiration(self, client, test_candidate, test_users):
        """تست انقضای VIP"""
        manager = VIPManager()
        user = test_users[0]
        
        # اعطای VIP با مدت خیلی کوتاه
        manager.award_vip_status(
            candidate_id=test_candidate.id,
            user_id=user.id,
            reason='تست',
            duration_months=0,  # انقضا فوری
            expires_at=datetime.now() - timedelta(days=1)  # دیروز منقضی شده
        )
        
        # چک کردن فعال بودن
        is_active = manager.is_vip_active(test_candidate.id, user.id)
        
        assert is_active is False
    
    def test_revoke_vip_status(self, client, test_candidate, test_users):
        """تست لغو وضعیت VIP"""
        manager = VIPManager()
        user = test_users[0]
        
        # اعطا و لغو
        manager.award_vip_status(
            test_candidate.id,
            user.id,
            'تست',
            duration_months=3
        )
        
        success = manager.revoke_vip_status(test_candidate.id, user.id)
        
        assert success is True
        
        # بررسی
        is_active = manager.is_vip_active(test_candidate.id, user.id)
        assert is_active is False


class TestVIPInteractions:
    """تست‌های تعامل با VIP ها"""
    
    def test_create_vip_interaction(self, client, test_candidate, test_users):
        """تست ایجاد تعامل VIP"""
        manager = VIPManager()
        user = test_users[0]
        
        # اعطای VIP
        manager.award_vip_status(test_candidate.id, user.id, 'تست', 3)
        
        # ایجاد تعامل
        interaction = manager.create_interaction(
            candidate_id=test_candidate.id,
            user_id=user.id,
            interaction_type='call',
            description='تماس تلفنی 30 دقیقه‌ای',
            points_awarded=50
        )
        
        assert interaction is not None
        assert interaction.interaction_type == 'call'
        assert interaction.points_awarded == 50
    
    def test_interaction_awards_points(self, client, test_candidate, test_users):
        """تست اعطای امتیاز در تعامل"""
        manager = VIPManager()
        user = test_users[0]
        
        manager.award_vip_status(test_candidate.id, user.id, 'تست', 3)
        
        # امتیاز اولیه
        initial_points = manager.get_total_points(test_candidate.id, user.id)
        
        # ایجاد تعامل با 100 امتیاز
        manager.create_interaction(
            test_candidate.id,
            user.id,
            'meeting',
            'جلسه حضوری',
            points_awarded=100
        )
        
        # امتیاز جدید
        new_points = manager.get_total_points(test_candidate.id, user.id)
        
        assert new_points == initial_points + 100


class TestVIPMeetings:
    """تست‌های جلسات VIP"""
    
    def test_schedule_vip_meeting(self, client, test_candidate, test_users):
        """تست زمان‌بندی جلسه VIP"""
        manager = VIPManager()
        user = test_users[0]
        
        manager.award_vip_status(test_candidate.id, user.id, 'تست', 3)
        
        # زمان‌بندی جلسه
        meeting = manager.schedule_meeting(
            candidate_id=test_candidate.id,
            user_id=user.id,
            meeting_date=datetime.now() + timedelta(days=7),
            duration_minutes=60,
            location='دفتر کاندید',
            topic='بررسی مسائل محلی'
        )
        
        assert meeting is not None
        assert meeting.status == 'scheduled'
        assert meeting.duration_minutes == 60
    
    def test_meeting_requires_availability(self, client, test_candidate, test_users):
        """تست چک کردن در دسترس بودن برای جلسه"""
        manager = VIPManager()
        user1 = test_users[0]
        user2 = test_users[1]
        
        manager.award_vip_status(test_candidate.id, user1.id, 'تست', 3)
        manager.award_vip_status(test_candidate.id, user2.id, 'تست', 3)
        
        # زمان‌بندی جلسه اول
        meeting_time = datetime.now() + timedelta(days=7)
        manager.schedule_meeting(
            test_candidate.id,
            user1.id,
            meeting_time,
            duration_minutes=60,
            location='دفتر'
        )
        
        # تلاش برای زمان‌بندی جلسه دوم در همان زمان
        is_available = manager.check_availability(
            test_candidate.id,
            meeting_time,
            duration_minutes=60
        )
        
        # نباید در دسترس باشه
        assert is_available is False
    
    def test_complete_meeting(self, client, test_candidate, test_users):
        """تست تکمیل جلسه"""
        manager = VIPManager()
        user = test_users[0]
        
        manager.award_vip_status(test_candidate.id, user.id, 'تست', 3)
        
        # زمان‌بندی جلسه
        meeting = manager.schedule_meeting(
            test_candidate.id,
            user.id,
            datetime.now() - timedelta(hours=1),  # در گذشته
            duration_minutes=60,
            location='دفتر'
        )
        
        # تکمیل جلسه
        success = manager.complete_meeting(
            meeting.id,
            notes='جلسه موفقی بود',
            points_awarded=150
        )
        
        assert success is True
        
        # بررسی وضعیت
        meeting = VIPMeeting.query.get(meeting.id)
        assert meeting.status == 'completed'
        assert meeting.points_awarded == 150
    
    def test_cancel_meeting(self, client, test_candidate, test_users):
        """تست کنسل کردن جلسه"""
        manager = VIPManager()
        user = test_users[0]
        
        manager.award_vip_status(test_candidate.id, user.id, 'تست', 3)
        
        meeting = manager.schedule_meeting(
            test_candidate.id,
            user.id,
            datetime.now() + timedelta(days=7),
            duration_minutes=60,
            location='دفتر'
        )
        
        # کنسل کردن
        success = manager.cancel_meeting(
            meeting.id,
            reason='تغییر برنامه'
        )
        
        assert success is True
        
        # بررسی
        meeting = VIPMeeting.query.get(meeting.id)
        assert meeting.status == 'cancelled'


class TestMonthlyTopCitizens:
    """تست‌های برترین شهروندان ماهانه"""
    
    def test_calculate_monthly_top_citizens(self, client, test_candidate, test_users):
        """تست محاسبه برترین‌ها"""
        manager = VIPManager()
        
        # اعطای VIP و امتیاز به چند کاربر
        for i in range(5):
            user = test_users[i]
            manager.award_vip_status(test_candidate.id, user.id, 'تست', 3)
            
            # امتیاز متفاوت
            points = (5 - i) * 100  # 500, 400, 300, 200, 100
            manager.create_interaction(
                test_candidate.id,
                user.id,
                'activity',
                'فعالیت',
                points_awarded=points
            )
        
        # محاسبه برترین‌ها
        top_citizens = manager.calculate_monthly_top_citizens(
            test_candidate.id,
            month=datetime.now().month,
            year=datetime.now().year,
            limit=3
        )
        
        assert len(top_citizens) == 3
        
        # بررسی ترتیب (امتیاز بالاتر اول)
        assert top_citizens[0]['points'] > top_citizens[1]['points']
        assert top_citizens[1]['points'] > top_citizens[2]['points']
    
    def test_save_monthly_top_citizens(self, client, test_candidate, test_users):
        """تست ذخیره برترین‌های ماهانه"""
        manager = VIPManager()
        
        # آماده‌سازی داده
        for i in range(3):
            user = test_users[i]
            manager.award_vip_status(test_candidate.id, user.id, 'تست', 3)
            manager.create_interaction(
                test_candidate.id,
                user.id,
                'activity',
                'فعالیت',
                points_awarded=(3 - i) * 100
            )
        
        # محاسبه و ذخیره
        top_citizens = manager.calculate_monthly_top_citizens(
            test_candidate.id,
            datetime.now().month,
            datetime.now().year,
            limit=10
        )
        
        success = manager.save_monthly_top_citizens(
            test_candidate.id,
            datetime.now().month,
            datetime.now().year,
            top_citizens
        )
        
        assert success is True
        
        # بررسی ذخیره
        saved = MonthlyTopCitizens.query.filter_by(
            candidate_id=test_candidate.id,
            month=datetime.now().month,
            year=datetime.now().year
        ).first()
        
        assert saved is not None


class TestVIPBenefits:
    """تست‌های مزایای VIP"""
    
    def test_vip_exclusive_access(self, client, test_candidate, test_users):
        """تست دسترسی اختصاصی VIP"""
        manager = VIPManager()
        vip_user = test_users[0]
        regular_user = test_users[1]
        
        # فقط یکی VIP است
        manager.award_vip_status(test_candidate.id, vip_user.id, 'تست', 3)
        
        # چک دسترسی VIP
        vip_has_access = manager.has_vip_access(test_candidate.id, vip_user.id)
        regular_has_access = manager.has_vip_access(test_candidate.id, regular_user.id)
        
        assert vip_has_access is True
        assert regular_has_access is False
    
    def test_vip_priority_support(self, client, test_candidate, test_users):
        """تست پشتیبانی اولویت‌دار VIP"""
        manager = VIPManager()
        vip_user = test_users[0]
        
        manager.award_vip_status(test_candidate.id, vip_user.id, 'تست', 3)
        
        # چک اولویت
        priority = manager.get_support_priority(test_candidate.id, vip_user.id)
        
        # VIP ها اولویت بالاتر دارن
        assert priority in ['high', 'vip']


class TestVIPStatistics:
    """تست‌های آمار VIP"""
    
    def test_get_total_vip_count(self, client, test_candidate, test_users):
        """تست شمارش کل VIP ها"""
        manager = VIPManager()
        
        # اعطای VIP به 5 نفر
        for i in range(5):
            manager.award_vip_status(test_candidate.id, test_users[i].id, 'تست', 3)
        
        # شمارش
        count = manager.get_total_vip_count(test_candidate.id)
        
        assert count == 5
    
    def test_get_vip_engagement_rate(self, client, test_candidate, test_users):
        """تست محاسبه نرخ تعامل VIP"""
        manager = VIPManager()
        
        # اعطای VIP و تعامل
        for i in range(3):
            manager.award_vip_status(test_candidate.id, test_users[i].id, 'تست', 3)
            
            if i < 2:  # فقط 2 نفر تعامل دارن
                manager.create_interaction(
                    test_candidate.id,
                    test_users[i].id,
                    'activity',
                    'فعالیت',
                    points_awarded=100
                )
        
        # نرخ تعامل
        engagement_rate = manager.get_engagement_rate(test_candidate.id)
        
        # 2 از 3 = 66.67%
        assert 60 <= engagement_rate <= 70


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
