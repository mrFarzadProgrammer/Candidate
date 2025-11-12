# -*- coding: utf-8 -*-
"""
Message Repository
==================
Repository برای عملیات مرتبط با پیام‌ها
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from database.models import Message, Candidate
from repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class MessageRepository(BaseRepository):
    """Repository برای مدیریت Messages"""
    
    model = Message
    
    @classmethod
    def get_by_candidate(cls, candidate_id: int, limit: int = 50, is_read: bool = None) -> List[Message]:
        """
        دریافت پیام‌های یک کاندیدا
        
        Args:
            candidate_id: شناسه کاندیدا
            limit: تعداد پیام‌ها
            is_read: فیلتر بر اساس خوانده/نخوانده
        """
        try:
            query = cls.model.query.filter_by(candidate_id=candidate_id)
            
            if is_read is not None:
                query = query.filter_by(is_read=is_read)
            
            return query.order_by(cls.model.created_at.desc()).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting messages by candidate: {e}")
            return []
    
    @classmethod
    def get_unread_count(cls, candidate_id: int) -> int:
        """تعداد پیام‌های خوانده نشده"""
        return cls.count(candidate_id=candidate_id, is_read=False)
    
    @classmethod
    def mark_as_read(cls, message_id: int) -> bool:
        """علامت‌گذاری پیام به عنوان خوانده شده"""
        return cls.update(message_id, is_read=True, read_at=datetime.now())
    
    @classmethod
    def mark_all_as_read(cls, candidate_id: int) -> int:
        """علامت‌گذاری همه پیام‌ها به عنوان خوانده شده"""
        try:
            from database.models import db
            from utils.db_utils import safe_commit
            
            count = cls.model.query.filter_by(
                candidate_id=candidate_id,
                is_read=False
            ).update({'is_read': True, 'read_at': datetime.now()})
            
            if safe_commit(db):
                logger.info(f"Marked {count} messages as read for candidate {candidate_id}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Error marking all as read: {e}")
            return 0
    
    @classmethod
    def get_today_messages(cls, candidate_id: int) -> List[Message]:
        """پیام‌های امروز"""
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            return cls.model.query.filter(
                cls.model.candidate_id == candidate_id,
                cls.model.created_at >= today_start
            ).all()
        except Exception as e:
            logger.error(f"Error getting today messages: {e}")
            return []
    
    @classmethod
    def get_statistics(cls, candidate_id: int) -> dict:
        """آمار پیام‌های یک کاندیدا"""
        try:
            return {
                'total': cls.count(candidate_id=candidate_id),
                'unread': cls.get_unread_count(candidate_id),
                'today': len(cls.get_today_messages(candidate_id)),
                'avg_response_time': cls._calculate_avg_response_time(candidate_id),
            }
        except Exception as e:
            logger.error(f"Error getting message statistics: {e}")
            return {}
    
    @classmethod
    def _calculate_avg_response_time(cls, candidate_id: int) -> float:
        """محاسبه میانگین زمان پاسخگویی (به ساعت)"""
        try:
            from database.models import db
            
            # پیام‌های پاسخ داده شده
            messages = cls.model.query.filter(
                cls.model.candidate_id == candidate_id,
                cls.model.is_read == True,
                cls.model.read_at != None
            ).all()
            
            if not messages:
                return 0.0
            
            total_seconds = sum([
                (msg.read_at - msg.created_at).total_seconds()
                for msg in messages
            ])
            
            avg_seconds = total_seconds / len(messages)
            return round(avg_seconds / 3600, 2)  # به ساعت
        except Exception as e:
            logger.error(f"Error calculating avg response time: {e}")
            return 0.0
