# -*- coding: utf-8 -*-
"""
Base Repository Pattern
=======================
کلاس پایه برای همه repository ها با عملیات CRUD استاندارد
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Query
from database.models import db
from utils.db_utils import safe_commit
import logging

logger = logging.getLogger(__name__)


class BaseRepository:
    """
    Repository پایه با عملیات CRUD استاندارد
    
    Usage:
        class CandidateRepository(BaseRepository):
            model = Candidate
    """
    
    model = None  # باید در subclass مشخص شود
    
    @classmethod
    def get_by_id(cls, id: int) -> Optional[Any]:
        """
        دریافت یک رکورد با ID
        
        Args:
            id: شناسه رکورد
        
        Returns:
            Object یا None
        """
        try:
            return cls.model.query.get(id)
        except Exception as e:
            logger.error(f"Error in get_by_id: {e}", exc_info=True)
            return None
    
    @classmethod
    def get_all(cls, filters: Dict = None, order_by=None, limit: int = None) -> List[Any]:
        """
        دریافت همه رکوردها با فیلتر و مرتب‌سازی
        
        Args:
            filters: دیکشنری از فیلترها {field: value}
            order_by: فیلد برای مرتب‌سازی
            limit: محدودیت تعداد
        
        Returns:
            لیست از objects
        
        Example:
            candidates = CandidateRepository.get_all(
                filters={'is_active': True},
                order_by='created_at',
                limit=10
            )
        """
        try:
            query = cls.model.query
            
            # Apply filters
            if filters:
                query = query.filter_by(**filters)
            
            # Apply ordering
            if order_by:
                if order_by.startswith('-'):
                    # Descending order
                    field = order_by[1:]
                    query = query.order_by(getattr(cls.model, field).desc())
                else:
                    # Ascending order
                    query = query.order_by(getattr(cls.model, order_by))
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except Exception as e:
            logger.error(f"Error in get_all: {e}", exc_info=True)
            return []
    
    @classmethod
    def create(cls, **kwargs) -> Optional[Any]:
        """
        ایجاد رکورد جدید
        
        Args:
            **kwargs: فیلدهای مدل
        
        Returns:
            Object ایجاد شده یا None
        
        Example:
            candidate = CandidateRepository.create(
                username='test',
                full_name='Test User'
            )
        """
        try:
            obj = cls.model(**kwargs)
            db.session.add(obj)
            
            if safe_commit(db, f"Failed to create {cls.model.__name__}"):
                logger.info(f"Created {cls.model.__name__} with id={obj.id}")
                return obj
            return None
        except Exception as e:
            logger.error(f"Error in create: {e}", exc_info=True)
            db.session.rollback()
            return None
    
    @classmethod
    def update(cls, id: int, **kwargs) -> bool:
        """
        آپدیت رکورد موجود
        
        Args:
            id: شناسه رکورد
            **kwargs: فیلدهای برای آپدیت
        
        Returns:
            True اگر موفق، False اگر ناموفق
        
        Example:
            success = CandidateRepository.update(
                id=1,
                full_name='New Name',
                bio='Updated bio'
            )
        """
        try:
            obj = cls.get_by_id(id)
            if not obj:
                logger.warning(f"{cls.model.__name__} with id={id} not found")
                return False
            
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            
            if safe_commit(db, f"Failed to update {cls.model.__name__}"):
                logger.info(f"Updated {cls.model.__name__} id={id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error in update: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    @classmethod
    def delete(cls, id: int) -> bool:
        """
        حذف رکورد
        
        Args:
            id: شناسه رکورد
        
        Returns:
            True اگر موفق، False اگر ناموفق
        """
        try:
            obj = cls.get_by_id(id)
            if not obj:
                logger.warning(f"{cls.model.__name__} with id={id} not found")
                return False
            
            db.session.delete(obj)
            
            if safe_commit(db, f"Failed to delete {cls.model.__name__}"):
                logger.info(f"Deleted {cls.model.__name__} id={id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error in delete: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    @classmethod
    def exists(cls, **filters) -> bool:
        """
        چک کردن وجود رکورد با فیلتر
        
        Args:
            **filters: فیلترهای جستجو
        
        Returns:
            True اگر وجود داشته باشد
        
        Example:
            exists = CandidateRepository.exists(username='test')
        """
        try:
            return cls.model.query.filter_by(**filters).first() is not None
        except Exception as e:
            logger.error(f"Error in exists: {e}", exc_info=True)
            return False
    
    @classmethod
    def count(cls, **filters) -> int:
        """
        شمارش رکوردها با فیلتر
        
        Args:
            **filters: فیلترهای جستجو
        
        Returns:
            تعداد رکوردها
        """
        try:
            query = cls.model.query
            if filters:
                query = query.filter_by(**filters)
            return query.count()
        except Exception as e:
            logger.error(f"Error in count: {e}", exc_info=True)
            return 0
    
    @classmethod
    def paginate(cls, page: int = 1, per_page: int = 20, **filters) -> Dict:
        """
        دریافت رکوردها با pagination
        
        Args:
            page: شماره صفحه (از 1 شروع می‌شود)
            per_page: تعداد در هر صفحه
            **filters: فیلترهای جستجو
        
        Returns:
            Dict با items, total, pages, page, per_page
        """
        try:
            query = cls.model.query
            if filters:
                query = query.filter_by(**filters)
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                'items': pagination.items,
                'total': pagination.total,
                'pages': pagination.pages,
                'page': page,
                'per_page': per_page,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
            }
        except Exception as e:
            logger.error(f"Error in paginate: {e}", exc_info=True)
            return {
                'items': [],
                'total': 0,
                'pages': 0,
                'page': page,
                'per_page': per_page,
                'has_prev': False,
                'has_next': False,
            }
