"""
سیستم مدیریت مرحله‌ای پلن‌ها
Gradual Plan Release Management
"""

from database.models import db, Plan, PlanPurchase, Candidate
from datetime import datetime
import logging

logger = logging.getLogger('plan_management')


# ============================================================
# 1. PLAN AVAILABILITY CONTROL
# ============================================================

class PlanManager:
    """مدیریت فعال‌سازی مرحله‌ای پلن‌ها"""
    
    # وضعیت‌های ممکن پلن
    STATUS_HIDDEN = 'hidden'  # پنهان - هنوز آماده نیست
    STATUS_BETA = 'beta'  # بتا - فقط کاربران خاص
    STATUS_ACTIVE = 'active'  # فعال - همه می‌توانند بخرند
    STATUS_DEPRECATED = 'deprecated'  # منسوخ - قابل خرید نیست
    
    def __init__(self):
        pass
    
    def get_available_plans(self, candidate_id=None):
        """
        دریافت پلن‌های قابل خرید
        
        Args:
            candidate_id: اگر داده شود، بتا تسترها هم می‌بینند
        
        Returns:
            list: لیست پلن‌های قابل نمایش
        """
        # پلن‌های active برای همه
        plans = Plan.query.filter_by(
            is_available=True,
            status=self.STATUS_ACTIVE
        ).all()
        
        # اگر کاربر beta tester است
        if candidate_id and self._is_beta_tester(candidate_id):
            beta_plans = Plan.query.filter_by(
                is_available=True,
                status=self.STATUS_BETA
            ).all()
            plans.extend(beta_plans)
        
        return plans
    
    def activate_plan(self, plan_code, status=STATUS_ACTIVE, notify_users=True):
        """
        فعال‌سازی پلن
        
        Args:
            plan_code: کد پلن (basic, standard, premium, enterprise)
            status: وضعیت (active, beta)
            notify_users: آیا به کاربران اعلان برود؟
        
        Returns:
            bool: موفق یا خیر
        """
        plan = Plan.query.filter_by(code=plan_code).first()
        
        if not plan:
            logger.error(f'Plan not found: {plan_code}')
            return False
        
        plan.status = status
        plan.is_available = True
        plan.activated_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f'Plan activated: {plan_code} with status {status}')
        
        # ارسال اعلان
        if notify_users and status == self.STATUS_ACTIVE:
            self._notify_plan_launch(plan)
        
        return True
    
    def deactivate_plan(self, plan_code):
        """غیرفعال کردن پلن"""
        plan = Plan.query.filter_by(code=plan_code).first()
        
        if plan:
            plan.status = self.STATUS_DEPRECATED
            plan.is_available = False
            db.session.commit()
            
            logger.info(f'Plan deactivated: {plan_code}')
            return True
        
        return False
    
    def set_plan_beta(self, plan_code):
        """قرار دادن پلن در حالت بتا"""
        return self.activate_plan(plan_code, status=self.STATUS_BETA, notify_users=False)
    
    def promote_plan_to_active(self, plan_code):
        """ارتقا از بتا به active"""
        plan = Plan.query.filter_by(code=plan_code).first()
        
        if not plan:
            return False
        
        if plan.status != self.STATUS_BETA:
            logger.warning(f'Plan {plan_code} is not in beta status')
            return False
        
        return self.activate_plan(plan_code, status=self.STATUS_ACTIVE, notify_users=True)
    
    def _is_beta_tester(self, candidate_id):
        """بررسی beta tester بودن"""
        candidate = Candidate.query.get(candidate_id)
        return candidate and candidate.is_beta_tester if hasattr(candidate, 'is_beta_tester') else False
    
    def _notify_plan_launch(self, plan):
        """اعلان فعال‌سازی پلن به کاربران"""
        from bot_engine.broadcast_sender import send_system_announcement
        
        message = f"""
🎉 پلن جدید {plan.name} فعال شد!

✨ ویژگی‌ها:
• {plan.max_subscribers} مخاطب
• {plan.max_messages_per_day} پیام در روز
• {plan.max_channels} کانال

💰 قیمت: {plan.price:,} تومان / {plan.duration_days} روز

برای خرید به پنل مراجعه کنید.
        """
        
        # ارسال به همه
        send_system_announcement(message)


# ============================================================
# 2. BETA TESTER MANAGEMENT
# ============================================================

class BetaTesterManager:
    """مدیریت کاربران آزمایشی"""
    
    def __init__(self):
        pass
    
    def add_beta_tester(self, candidate_id, plan_code=None):
        """
        افزودن beta tester
        
        Args:
            candidate_id: ID نامزد
            plan_code: پلن خاص (اختیاری)
        """
        from database.models import BetaTester
        
        tester = BetaTester(
            candidate_id=candidate_id,
            plan_code=plan_code,
            added_at=datetime.utcnow()
        )
        
        db.session.add(tester)
        
        # flag در Candidate
        candidate = Candidate.query.get(candidate_id)
        if candidate:
            candidate.is_beta_tester = True
        
        db.session.commit()
        
        logger.info(f'Beta tester added: candidate {candidate_id}')
    
    def remove_beta_tester(self, candidate_id):
        """حذف از beta testers"""
        from database.models import BetaTester
        
        BetaTester.query.filter_by(candidate_id=candidate_id).delete()
        
        candidate = Candidate.query.get(candidate_id)
        if candidate:
            candidate.is_beta_tester = False
        
        db.session.commit()
    
    def get_beta_testers(self, plan_code=None):
        """لیست beta testers"""
        from database.models import BetaTester
        
        query = BetaTester.query
        
        if plan_code:
            query = query.filter_by(plan_code=plan_code)
        
        return query.all()
    
    def grant_free_access(self, candidate_id, plan_code, duration_days=30):
        """
        اعطای دسترسی رایگان برای تست
        """
        plan = Plan.query.filter_by(code=plan_code).first()
        
        if not plan:
            return False
        
        purchase = PlanPurchase(
            candidate_id=candidate_id,
            plan_id=plan.id,
            payment_amount=0,  # رایگان
            payment_status='completed',
            is_trial=False,
            is_beta_access=True,
            purchase_date=datetime.utcnow(),
            expiry_date=datetime.utcnow() + timedelta(days=duration_days)
        )
        
        db.session.add(purchase)
        db.session.commit()
        
        logger.info(f'Free beta access granted: candidate {candidate_id}, plan {plan_code}, {duration_days} days')
        return True


# ============================================================
# 3. PLAN ROLLOUT STRATEGY
# ============================================================

class PlanRollout:
    """استراتژی راه‌اندازی مرحله‌ای"""
    
    # مراحل راه‌اندازی
    PHASE_1 = 'phase_1'  # پلن پایه فقط
    PHASE_2 = 'phase_2'  # پایه + استاندارد
    PHASE_3 = 'phase_3'  # پایه + استاندارد + پرمیوم (بتا)
    PHASE_4 = 'phase_4'  # همه پلن‌ها فعال
    
    def __init__(self):
        self.plan_manager = PlanManager()
    
    def execute_phase_1(self):
        """
        فاز 1: فقط Basic Plan
        """
        logger.info('Executing Phase 1: Basic Plan Only')
        
        # فعال کردن Basic
        self.plan_manager.activate_plan('basic', status=PlanManager.STATUS_ACTIVE)
        
        # بقیه پنهان
        self.plan_manager.deactivate_plan('standard')
        self.plan_manager.deactivate_plan('premium')
        self.plan_manager.deactivate_plan('enterprise')
        
        self._set_current_phase(self.PHASE_1)
    
    def execute_phase_2(self):
        """
        فاز 2: Basic + Standard
        """
        logger.info('Executing Phase 2: Basic + Standard')
        
        self.plan_manager.activate_plan('basic')
        self.plan_manager.activate_plan('standard')
        
        # Premium بتا
        self.plan_manager.set_plan_beta('premium')
        
        self.plan_manager.deactivate_plan('enterprise')
        
        self._set_current_phase(self.PHASE_2)
    
    def execute_phase_3(self):
        """
        فاز 3: Basic + Standard + Premium (Beta)
        """
        logger.info('Executing Phase 3: With Premium Beta')
        
        self.plan_manager.activate_plan('basic')
        self.plan_manager.activate_plan('standard')
        self.plan_manager.set_plan_beta('premium')
        
        self.plan_manager.deactivate_plan('enterprise')
        
        self._set_current_phase(self.PHASE_3)
    
    def execute_phase_4(self):
        """
        فاز 4: تمام پلن‌ها فعال
        """
        logger.info('Executing Phase 4: All Plans Active')
        
        self.plan_manager.activate_plan('basic')
        self.plan_manager.activate_plan('standard')
        self.plan_manager.promote_plan_to_active('premium')
        self.plan_manager.activate_plan('enterprise')
        
        self._set_current_phase(self.PHASE_4)
    
    def get_current_phase(self):
        """دریافت فاز فعلی"""
        from database.models import SystemConfig
        
        config = SystemConfig.query.filter_by(key='current_rollout_phase').first()
        return config.value if config else self.PHASE_1
    
    def _set_current_phase(self, phase):
        """تنظیم فاز فعلی"""
        from database.models import SystemConfig
        
        config = SystemConfig.query.filter_by(key='current_rollout_phase').first()
        
        if config:
            config.value = phase
            config.updated_at = datetime.utcnow()
        else:
            config = SystemConfig(
                key='current_rollout_phase',
                value=phase,
                created_at=datetime.utcnow()
            )
            db.session.add(config)
        
        db.session.commit()


# ============================================================
# 4. PLAN MIGRATION (ارتقا/تنزل)
# ============================================================

class PlanMigration:
    """مدیریت تغییر پلن کاربران"""
    
    def upgrade_plan(self, candidate_id, new_plan_code):
        """ارتقا پلن"""
        # logic ارتقا...
        pass
    
    def downgrade_plan(self, candidate_id, new_plan_code):
        """تنزل پلن"""
        # logic تنزل...
        pass


# ============================================================
# 5. PLAN PRICING CONTROL
# ============================================================

class PricingManager:
    """مدیریت قیمت‌گذاری"""
    
    def set_plan_price(self, plan_code, new_price):
        """تغییر قیمت پلن"""
        plan = Plan.query.filter_by(code=plan_code).first()
        
        if plan:
            old_price = plan.price
            plan.price = new_price
            plan.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f'Price changed for {plan_code}: {old_price} -> {new_price}')
            return True
        
        return False
    
    def create_discount_campaign(self, plan_code, discount_percent, start_date, end_date):
        """کمپین تخفیف"""
        from database.models import DiscountCampaign
        
        campaign = DiscountCampaign(
            plan_code=plan_code,
            discount_percent=discount_percent,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        logger.info(f'Discount campaign created: {plan_code} - {discount_percent}%')
