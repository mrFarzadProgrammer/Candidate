# -*- coding: utf-8 -*-
"""
تست‌های سیستم انتشار تدریجی پلن‌ها
Gradual Plan Release System Tests
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from admin_panel.app import app, db
from database.models import Plan, Candidate, PlanAvailability, BetaTester, DiscountCampaign
from plan_management.gradual_release import PlanReleaseManager
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
def test_plans():
    """فیکسچر پلن‌های تست"""
    with app.app_context():
        plans = []
        for i in range(5):
            plan = Plan(
                name=f'پلن {i}',
                name_en=f'Plan {i}',
                price=1000000 * (i + 1),
                duration_months=i + 1,
                max_users=(i + 1) * 1000,
                is_active=False  # همه غیرفعال شروع می‌کنن
            )
            db.session.add(plan)
            plans.append(plan)
        
        db.session.commit()
        return plans


@pytest.fixture
def test_candidates():
    """فیکسچر کاندیدهای تست"""
    with app.app_context():
        candidates = []
        for i in range(10):
            candidate = Candidate(
                name=f'کاندید {i}',
                username=f'candidate_{i}',
                password=hash_password('Pass123'),
                telegram_token=f'123{i}:ABC',
                bot_username=f'bot_{i}'
            )
            db.session.add(candidate)
            candidates.append(candidate)
        
        db.session.commit()
        return candidates


class TestPlanEnableDisable:
    """تست‌های فعال/غیرفعال کردن پلن"""
    
    def test_enable_plan_makes_available(self, client, test_plans):
        """تست فعال کردن پلن"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        
        # فعال کردن پلن
        success = manager.enable_plan(plan.id)
        
        assert success is True
        
        # بررسی وضعیت
        plan = Plan.query.get(plan.id)
        assert plan.is_active is True
    
    def test_disable_plan_hides_from_users(self, client, test_plans):
        """تست غیرفعال کردن پلن"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        
        # ابتدا فعال کن
        manager.enable_plan(plan.id)
        
        # سپس غیرفعال کن
        success = manager.disable_plan(plan.id)
        
        assert success is True
        
        # بررسی وضعیت
        plan = Plan.query.get(plan.id)
        assert plan.is_active is False
    
    def test_enable_plan_for_specific_regions(self, client, test_plans):
        """تست فعال کردن پلن برای مناطق خاص"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        
        # فعال کردن فقط برای تهران و اصفهان
        success = manager.enable_plan(
            plan.id,
            regions=['Tehran', 'Isfahan']
        )
        
        assert success is True
        
        # بررسی availability
        availability = PlanAvailability.query.filter_by(plan_id=plan.id).first()
        assert availability is not None
        assert 'Tehran' in availability.regions
        assert 'Isfahan' in availability.regions


class TestScheduledRelease:
    """تست‌های انتشار زمان‌بندی شده"""
    
    def test_schedule_plan_release(self, client, test_plans):
        """تست زمان‌بندی انتشار پلن"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        
        # زمان‌بندی برای 1 ساعت بعد
        release_time = datetime.now() + timedelta(hours=1)
        
        success = manager.schedule_plan_release(
            plan.id,
            release_time=release_time
        )
        
        assert success is True
        
        # بررسی schedule
        availability = PlanAvailability.query.filter_by(plan_id=plan.id).first()
        assert availability is not None
        assert availability.scheduled_release is not None
    
    def test_scheduled_release_activates_on_time(self, client, test_plans):
        """تست فعال شدن پلن در زمان تعیین شده"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        
        # زمان‌بندی برای 1 ثانیه بعد
        release_time = datetime.now() + timedelta(seconds=1)
        
        manager.schedule_plan_release(plan.id, release_time=release_time)
        
        # چک کن که فعلاً غیرفعال است
        plan = Plan.query.get(plan.id)
        assert plan.is_active is False
        
        # صبر کن تا زمان برسه
        import time
        time.sleep(2)
        
        # اجرای task پردازش schedule ها
        manager.process_scheduled_releases()
        
        # چک کن که فعال شده
        plan = Plan.query.get(plan.id)
        assert plan.is_active is True
    
    def test_cancel_scheduled_release(self, client, test_plans):
        """تست لغو زمان‌بندی"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        
        # زمان‌بندی
        release_time = datetime.now() + timedelta(hours=1)
        manager.schedule_plan_release(plan.id, release_time=release_time)
        
        # لغو
        success = manager.cancel_scheduled_release(plan.id)
        
        assert success is True
        
        # بررسی
        availability = PlanAvailability.query.filter_by(plan_id=plan.id).first()
        assert availability.scheduled_release is None


class TestBetaTesters:
    """تست‌های beta tester ها"""
    
    def test_add_beta_tester(self, client, test_plans, test_candidates):
        """تست اضافه کردن beta tester"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        candidate = test_candidates[0]
        
        # اضافه کردن beta tester
        success = manager.add_beta_tester(plan.id, candidate.id)
        
        assert success is True
        
        # بررسی
        beta_tester = BetaTester.query.filter_by(
            plan_id=plan.id,
            candidate_id=candidate.id
        ).first()
        assert beta_tester is not None
    
    def test_beta_tester_can_access_unreleased_plan(self, client, test_plans, test_candidates):
        """تست دسترسی beta tester به پلن منتشر نشده"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        candidate = test_candidates[0]
        
        # پلن غیرفعال است
        assert plan.is_active is False
        
        # اضافه کردن beta tester
        manager.add_beta_tester(plan.id, candidate.id)
        
        # چک دسترسی
        has_access = manager.can_access_plan(candidate.id, plan.id)
        
        assert has_access is True
    
    def test_regular_user_cannot_access_unreleased_plan(self, client, test_plans, test_candidates):
        """تست عدم دسترسی کاربر عادی به پلن منتشر نشده"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        candidate = test_candidates[0]
        
        # پلن غیرفعال است
        assert plan.is_active is False
        
        # چک دسترسی (بدون beta tester بودن)
        has_access = manager.can_access_plan(candidate.id, plan.id)
        
        assert has_access is False
    
    def test_remove_beta_tester(self, client, test_plans, test_candidates):
        """تست حذف beta tester"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        candidate = test_candidates[0]
        
        # اضافه و حذف
        manager.add_beta_tester(plan.id, candidate.id)
        success = manager.remove_beta_tester(plan.id, candidate.id)
        
        assert success is True
        
        # بررسی
        beta_tester = BetaTester.query.filter_by(
            plan_id=plan.id,
            candidate_id=candidate.id
        ).first()
        assert beta_tester is None


class TestDiscountCampaigns:
    """تست‌های کمپین‌های تخفیف"""
    
    def test_create_discount_campaign(self, client, test_plans):
        """تست ایجاد کمپین تخفیف"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        
        # ایجاد کمپین 20% تخفیف
        campaign = manager.create_discount_campaign(
            plan_id=plan.id,
            discount_percent=20,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            description='تخفیف ویژه هفته اول'
        )
        
        assert campaign is not None
        assert campaign.discount_percent == 20
        assert campaign.is_active is True
    
    def test_discount_applies_correctly(self, client, test_plans):
        """تست اعمال صحیح تخفیف"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        original_price = plan.price
        
        # ایجاد کمپین 25% تخفیف
        manager.create_discount_campaign(
            plan_id=plan.id,
            discount_percent=25,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        # محاسبه قیمت با تخفیف
        discounted_price = manager.get_discounted_price(plan.id)
        
        expected_price = original_price * 0.75  # 25% تخفیف
        assert discounted_price == expected_price
    
    def test_expired_discount_not_applied(self, client, test_plans):
        """تست عدم اعمال تخفیف منقضی شده"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        original_price = plan.price
        
        # ایجاد کمپین منقضی شده
        manager.create_discount_campaign(
            plan_id=plan.id,
            discount_percent=20,
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now() - timedelta(days=1)  # دیروز تمام شده
        )
        
        # قیمت باید بدون تخفیف باشه
        discounted_price = manager.get_discounted_price(plan.id)
        
        assert discounted_price == original_price
    
    def test_multiple_discounts_highest_applied(self, client, test_plans):
        """تست اعمال بالاترین تخفیف در صورت چند کمپین"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        
        # ایجاد چند کمپین
        manager.create_discount_campaign(
            plan_id=plan.id,
            discount_percent=15,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        manager.create_discount_campaign(
            plan_id=plan.id,
            discount_percent=30,  # بیشترین تخفیف
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        manager.create_discount_campaign(
            plan_id=plan.id,
            discount_percent=10,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7)
        )
        
        # باید 30% تخفیف اعمال بشه
        discounted_price = manager.get_discounted_price(plan.id)
        expected_price = plan.price * 0.7  # 30% تخفیف
        
        assert discounted_price == expected_price


class TestGradualRollout:
    """تست‌های rollout تدریجی"""
    
    def test_gradual_rollout_percentage(self, client, test_plans, test_candidates):
        """تست rollout به درصد مشخص کاربران"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        
        # rollout به 20% کاربران
        success = manager.start_gradual_rollout(
            plan.id,
            percentage=20
        )
        
        assert success is True
        
        # چک کنیم چند نفر دسترسی دارن
        accessible_count = sum(
            1 for candidate in test_candidates
            if manager.can_access_plan(candidate.id, plan.id)
        )
        
        # باید حدود 20% باشه (2 نفر از 10 نفر)
        assert 1 <= accessible_count <= 3
    
    def test_rollout_increase_over_time(self, client, test_plans, test_candidates):
        """تست افزایش تدریجی rollout"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        
        # شروع با 20%
        manager.start_gradual_rollout(plan.id, percentage=20)
        
        initial_count = sum(
            1 for candidate in test_candidates
            if manager.can_access_plan(candidate.id, plan.id)
        )
        
        # افزایش به 50%
        manager.increase_rollout_percentage(plan.id, percentage=50)
        
        increased_count = sum(
            1 for candidate in test_candidates
            if manager.can_access_plan(candidate.id, plan.id)
        )
        
        # تعداد دسترسی باید بیشتر شده باشه
        assert increased_count > initial_count
    
    def test_complete_rollout(self, client, test_plans, test_candidates):
        """تست rollout کامل به همه کاربران"""
        manager = PlanReleaseManager()
        plan = test_plans[0]
        
        # rollout کامل
        success = manager.complete_rollout(plan.id)
        
        assert success is True
        
        # همه باید دسترسی داشته باشن
        accessible_count = sum(
            1 for candidate in test_candidates
            if manager.can_access_plan(candidate.id, plan.id)
        )
        
        assert accessible_count == len(test_candidates)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
