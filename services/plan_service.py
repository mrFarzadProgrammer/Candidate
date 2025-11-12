# -*- coding: utf-8 -*-
"""
Plan Service
============
سرویس مدیریت پلن‌ها و خریدها
"""

from typing import Optional, Dict, List
from datetime import datetime
from repositories.plan_repository import PlanRepository, PlanPurchaseRepository
from repositories.candidate_repository import CandidateRepository
import logging

logger = logging.getLogger(__name__)


class PlanService:
    """سرویس مدیریت پلن‌ها"""
    
    @staticmethod
    def get_available_plans() -> List:
        """دریافت پلن‌های قابل خرید"""
        try:
            plans = PlanRepository.get_available_for_purchase()
            logger.info(f"Retrieved {len(plans)} available plans")
            return plans
        except Exception as e:
            logger.error(f"Error getting available plans: {e}")
            return []
    
    @staticmethod
    def get_plan_details(plan_id: int) -> Optional[Dict]:
        """دریافت جزئیات کامل یک پلن"""
        try:
            plan = PlanRepository.get_by_id(plan_id)
            if not plan:
                return None
            
            return {
                'id': plan.id,
                'name': plan.name,
                'code': plan.code,
                'description': plan.description,
                'price': plan.price,
                'duration_days': plan.duration_days,
                'features': PlanService._extract_features(plan),
                'is_popular': plan.is_popular,
                'badge_color': plan.badge_color,
            }
        except Exception as e:
            logger.error(f"Error getting plan details: {e}")
            return None
    
    @staticmethod
    def _extract_features(plan) -> List[str]:
        """استخراج لیست امکانات پلن"""
        features = []
        
        if plan.max_messages != -1:
            features.append(f"حداکثر {plan.max_messages} پیام")
        else:
            features.append("پیام نامحدود")
        
        if plan.has_ai:
            features.append("امکانات هوش مصنوعی")
        
        if plan.can_mass_message:
            features.append("ارسال پیام دسته‌جمعی")
        
        if plan.has_analytics:
            features.append("آنالیتیکس و گزارش‌گیری")
        
        if plan.priority_support:
            features.append("پشتیبانی اولویت‌دار")
        
        return features
    
    @staticmethod
    def purchase_plan(candidate_id: int, plan_code: str, payment_info: Dict = None) -> Dict:
        """
        خرید پلن
        
        Args:
            candidate_id: شناسه کاندیدا
            plan_code: کد پلن
            payment_info: اطلاعات پرداخت (اختیاری)
        
        Returns:
            dict با success, message
        
        Example:
            result = PlanService.purchase_plan(
                candidate_id=1,
                plan_code='PROFESSIONAL',
                payment_info={'transaction_id': '123456'}
            )
        """
        try:
            # Validation
            candidate = CandidateRepository.get_by_id(candidate_id)
            if not candidate:
                return {
                    'success': False,
                    'message': 'کاندیدا یافت نشد'
                }
            
            plan = PlanRepository.get_by_code(plan_code)
            if not plan or not plan.is_active:
                return {
                    'success': False,
                    'message': 'پلن معتبر نیست یا غیرفعال است'
                }
            
            # Check if already has active plan
            active_purchase = PlanPurchaseRepository.get_active_purchase(candidate_id)
            if active_purchase:
                return {
                    'success': False,
                    'message': f'شما هم‌اکنون پلن {active_purchase.plan.name} فعال دارید'
                }
            
            # Create purchase
            purchase = PlanPurchaseRepository.create_purchase(
                candidate_id=candidate_id,
                plan_id=plan.id,
                price=plan.price
            )
            
            if not purchase:
                return {
                    'success': False,
                    'message': 'خطا در ثبت خرید'
                }
            
            # Process referral rewards if applicable
            try:
                from candidate_panel.referral_utils import process_conversion_reward
                process_conversion_reward(candidate_id)
            except:
                pass  # Referral system is optional
            
            logger.info(f"Plan {plan.code} purchased by candidate {candidate_id}")
            
            return {
                'success': True,
                'message': f'پلن {plan.name} با موفقیت خریداری شد',
                'purchase_id': purchase.id,
                'expires_at': purchase.expires_at
            }
            
        except Exception as e:
            logger.error(f"Error purchasing plan: {e}", exc_info=True)
            return {
                'success': False,
                'message': 'خطا در خرید پلن'
            }
    
    @staticmethod
    def get_candidate_subscription(candidate_id: int) -> Optional[Dict]:
        """دریافت اشتراک فعلی کاندیدا"""
        try:
            purchase = PlanPurchaseRepository.get_active_purchase(candidate_id)
            if not purchase:
                return None
            
            # Calculate days remaining
            days_remaining = (purchase.expires_at - datetime.now()).days
            
            return {
                'plan_name': purchase.plan.name,
                'plan_code': purchase.plan.code,
                'purchased_at': purchase.purchased_at,
                'expires_at': purchase.expires_at,
                'days_remaining': max(0, days_remaining),
                'is_active': purchase.is_active and days_remaining > 0,
                'features': PlanService._extract_features(purchase.plan)
            }
        except Exception as e:
            logger.error(f"Error getting subscription: {e}")
            return None
    
    @staticmethod
    def check_feature_access(candidate_id: int, feature_code: str) -> bool:
        """
        بررسی دسترسی به یک امکان خاص
        
        Args:
            candidate_id: شناسه کاندیدا
            feature_code: کد امکان (has_ai, can_mass_message, etc.)
        
        Returns:
            True اگر دسترسی دارد
        """
        try:
            purchase = PlanPurchaseRepository.get_active_purchase(candidate_id)
            if not purchase:
                return False
            
            return getattr(purchase.plan, feature_code, False)
        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return False
    
    @staticmethod
    def renew_plan(candidate_id: int) -> Dict:
        """تمدید پلن فعلی"""
        try:
            current = PlanPurchaseRepository.get_active_purchase(candidate_id)
            if not current:
                return {
                    'success': False,
                    'message': 'اشتراک فعالی یافت نشد'
                }
            
            # Create new purchase with same plan
            new_purchase = PlanPurchaseRepository.create_purchase(
                candidate_id=candidate_id,
                plan_id=current.plan_id,
                price=current.plan.price
            )
            
            if new_purchase:
                # Deactivate old purchase
                PlanPurchaseRepository.update(current.id, is_active=False)
                
                logger.info(f"Plan renewed for candidate {candidate_id}")
                return {
                    'success': True,
                    'message': 'پلن با موفقیت تمدید شد',
                    'new_expires_at': new_purchase.expires_at
                }
            
            return {
                'success': False,
                'message': 'خطا در تمدید پلن'
            }
            
        except Exception as e:
            logger.error(f"Error renewing plan: {e}", exc_info=True)
            return {
                'success': False,
                'message': 'خطا در تمدید پلن'
            }
