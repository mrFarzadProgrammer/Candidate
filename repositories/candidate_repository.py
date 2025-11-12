# -*- coding: utf-8 -*-
"""
Candidate Repository
====================
Repository برای عملیات مرتبط با Candidate
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import func, and_, or_
from database.models import Candidate, PlanPurchase, Plan
from repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class CandidateRepository(BaseRepository):
    """Repository برای مدیریت Candidates"""
    
    model = Candidate
    
    @classmethod
    def get_by_username(cls, username: str) -> Optional[Candidate]:
        """دریافت کاندیدا با username"""
        try:
            return cls.model.query.filter_by(username=username).first()
        except Exception as e:
            logger.error(f"Error getting candidate by username: {e}")
            return None
    
    @classmethod
    def get_active_candidates(cls, limit: int = None) -> List[Candidate]:
        """دریافت کاندیداهای فعال"""
        return cls.get_all(filters={'is_active': True}, limit=limit)
    
    @classmethod
    def get_by_province(cls, province: str, city: str = None) -> List[Candidate]:
        """دریافت کاندیداها بر اساس استان و شهر"""
        try:
            query = cls.model.query.filter_by(province=province, is_active=True)
            if city:
                query = query.filter_by(city=city)
            return query.all()
        except Exception as e:
            logger.error(f"Error getting candidates by location: {e}")
            return []
    
    @classmethod
    def get_with_active_plan(cls, candidate_id: int) -> Optional[Candidate]:
        """دریافت کاندیدا همراه با پلن فعال"""
        try:
            return cls.model.query\
                .join(PlanPurchase)\
                .filter(
                    cls.model.id == candidate_id,
                    PlanPurchase.is_active == True
                ).first()
        except Exception as e:
            logger.error(f"Error getting candidate with active plan: {e}")
            return None
    
    @classmethod
    def search(cls, query: str, filters: dict = None) -> List[Candidate]:
        """
        جستجو در کاندیداها
        
        Args:
            query: متن جستجو
            filters: فیلترهای اضافی
        """
        try:
            search_query = cls.model.query.filter(
                or_(
                    cls.model.full_name.contains(query),
                    cls.model.username.contains(query),
                    cls.model.bio.contains(query)
                )
            )
            
            if filters:
                search_query = search_query.filter_by(**filters)
            
            return search_query.all()
        except Exception as e:
            logger.error(f"Error searching candidates: {e}")
            return []
    
    @classmethod
    def get_statistics(cls) -> dict:
        """آمار کلی کاندیداها"""
        try:
            return {
                'total': cls.count(),
                'active': cls.count(is_active=True),
                'inactive': cls.count(is_active=False),
                'with_plan': cls._count_with_active_plan(),
            }
        except Exception as e:
            logger.error(f"Error getting candidate statistics: {e}")
            return {}
    
    @classmethod
    def _count_with_active_plan(cls) -> int:
        """شمارش کاندیداهای با پلن فعال"""
        try:
            from database.models import db
            return db.session.query(func.count(cls.model.id.distinct()))\
                .join(PlanPurchase)\
                .filter(PlanPurchase.is_active == True)\
                .scalar()
        except:
            return 0
