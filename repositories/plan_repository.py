# -*- coding: utf-8 -*-
"""
Plan Repository
===============
Repository برای عملیات مرتبط با پلن‌ها و خریدها
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import func, and_
from database.models import Plan, PlanPurchase, Candidate
from repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class PlanRepository(BaseRepository):
    """Repository برای مدیریت Plans"""
    
    model = Plan
    
    @classmethod
    def get_active_plans(cls) -> List[Plan]:
        """دریافت پلن‌های فعال"""
        return cls.get_all(
            filters={'is_active': True},
            order_by='display_order'
        )
    
    @classmethod
    def get_by_code(cls, code: str) -> Optional[Plan]:
        """دریافت پلن با کد"""
        try:
            return cls.model.query.filter_by(code=code.upper()).first()
        except Exception as e:
            logger.error(f"Error getting plan by code: {e}")
            return None
    
    @classmethod
    def get_available_for_purchase(cls) -> List[Plan]:
        """پلن‌های قابل خرید"""
        return cls.get_all(
            filters={
                'is_active': True,
                'is_available_for_purchase': True
            },
            order_by='display_order'
        )
    
    @classmethod
    def get_popular_plans(cls) -> List[Plan]:
        """پلن‌های محبوب"""
        return cls.get_all(
            filters={
                'is_active': True,
                'is_popular': True
            },
            order_by='display_order'
        )


class PlanPurchaseRepository(BaseRepository):
    """Repository برای مدیریت خریدهای پلن"""
    
    model = PlanPurchase
    
    @classmethod
    def get_active_purchase(cls, candidate_id: int) -> Optional[PlanPurchase]:
        """دریافت خرید فعال کاندیدا"""
        try:
            return cls.model.query.filter_by(
                candidate_id=candidate_id,
                is_active=True
            ).first()
        except Exception as e:
            logger.error(f"Error getting active purchase: {e}")
            return None
    
    @classmethod
    def get_by_candidate(cls, candidate_id: int) -> List[PlanPurchase]:
        """تاریخچه خریدهای یک کاندیدا"""
        try:
            return cls.model.query.filter_by(candidate_id=candidate_id)\
                .order_by(cls.model.purchased_at.desc())\
                .all()
        except Exception as e:
            logger.error(f"Error getting purchases by candidate: {e}")
            return []
    
    @classmethod
    def has_active_plan(cls, candidate_id: int, plan_code: str = None) -> bool:
        """
        چک کردن وجود پلن فعال
        
        Args:
            candidate_id: شناسه کاندیدا
            plan_code: کد پلن (اختیاری - برای چک پلن خاص)
        """
        try:
            query = cls.model.query.join(Plan).filter(
                cls.model.candidate_id == candidate_id,
                cls.model.is_active == True
            )
            
            if plan_code:
                query = query.filter(Plan.code == plan_code.upper())
            
            return query.first() is not None
        except Exception as e:
            logger.error(f"Error checking active plan: {e}")
            return False
    
    @classmethod
    def create_purchase(cls, candidate_id: int, plan_id: int, price: int = None) -> Optional[PlanPurchase]:
        """
        ایجاد خرید جدید
        
        Args:
            candidate_id: شناسه کاندیدا
            plan_id: شناسه پلن
            price: قیمت (اختیاری - از پلن گرفته می‌شود)
        """
        try:
            plan = PlanRepository.get_by_id(plan_id)
            if not plan:
                logger.error(f"Plan {plan_id} not found")
                return None
            
            # محاسبه تاریخ انقضا
            from datetime import timedelta
            expires_at = datetime.now() + timedelta(days=plan.duration_days)
            
            purchase = cls.create(
                candidate_id=candidate_id,
                plan_id=plan_id,
                price=price or plan.price,
                purchased_at=datetime.now(),
                expires_at=expires_at,
                is_active=True
            )
            
            return purchase
        except Exception as e:
            logger.error(f"Error creating purchase: {e}")
            return None
    
    @classmethod
    def deactivate_expired_plans(cls) -> int:
        """غیرفعال کردن پلن‌های منقضی شده"""
        try:
            from database.models import db
            from utils.db_utils import safe_commit
            
            count = cls.model.query.filter(
                cls.model.is_active == True,
                cls.model.expires_at < datetime.now()
            ).update({'is_active': False})
            
            if safe_commit(db):
                logger.info(f"Deactivated {count} expired plans")
                return count
            return 0
        except Exception as e:
            logger.error(f"Error deactivating expired plans: {e}")
            return 0
    
    @classmethod
    def get_statistics(cls) -> dict:
        """آمار خریدهای پلن"""
        try:
            from database.models import db
            
            return {
                'total_purchases': cls.count(),
                'active_subscriptions': cls.count(is_active=True),
                'expired_subscriptions': cls.model.query.filter(
                    cls.model.expires_at < datetime.now()
                ).count(),
                'revenue_total': db.session.query(func.sum(cls.model.price)).scalar() or 0,
            }
        except Exception as e:
            logger.error(f"Error getting purchase statistics: {e}")
            return {}
