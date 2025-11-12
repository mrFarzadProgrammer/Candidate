# -*- coding: utf-8 -*-
"""
Message Service
===============
سرویس مدیریت پیام‌ها
"""

from typing import Dict, List, Optional
from datetime import datetime
from repositories.message_repository import MessageRepository
from repositories.candidate_repository import CandidateRepository
import logging

logger = logging.getLogger(__name__)


class MessageService:
    """سرویس مدیریت پیام‌ها"""
    
    @staticmethod
    def get_messages(candidate_id: int, page: int = 1, per_page: int = 20, unread_only: bool = False) -> Dict:
        """
        دریافت پیام‌های یک کاندیدا با pagination
        
        Args:
            candidate_id: شناسه کاندیدا
            page: شماره صفحه
            per_page: تعداد در هر صفحه
            unread_only: فقط نخوانده‌ها
        
        Returns:
            dict با messages, pagination_info, statistics
        """
        try:
            is_read = False if unread_only else None
            messages = MessageRepository.get_by_candidate(
                candidate_id, 
                limit=per_page,
                is_read=is_read
            )
            
            stats = MessageRepository.get_statistics(candidate_id)
            
            return {
                'success': True,
                'messages': messages,
                'statistics': stats,
                'page': page,
                'per_page': per_page
            }
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return {
                'success': False,
                'messages': [],
                'statistics': {}
            }
    
    @staticmethod
    def mark_as_read(message_id: int, candidate_id: int) -> Dict:
        """
        علامت‌گذاری پیام به عنوان خوانده شده
        
        Args:
            message_id: شناسه پیام
            candidate_id: شناسه کاندیدا (برای security)
        
        Returns:
            dict با success و message
        """
        try:
            # Verify ownership
            message = MessageRepository.get_by_id(message_id)
            if not message:
                return {
                    'success': False,
                    'message': 'پیام یافت نشد'
                }
            
            if message.candidate_id != candidate_id:
                logger.warning(f"Unauthorized attempt to mark message {message_id} by candidate {candidate_id}")
                return {
                    'success': False,
                    'message': 'شما مجاز به خواندن این پیام نیستید'
                }
            
            if MessageRepository.mark_as_read(message_id):
                return {
                    'success': True,
                    'message': 'پیام به عنوان خوانده شده علامت‌گذاری شد'
                }
            
            return {
                'success': False,
                'message': 'خطا در علامت‌گذاری پیام'
            }
            
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return {
                'success': False,
                'message': 'خطا در علامت‌گذاری پیام'
            }
    
    @staticmethod
    def mark_all_as_read(candidate_id: int) -> Dict:
        """علامت‌گذاری همه پیام‌ها به عنوان خوانده شده"""
        try:
            count = MessageRepository.mark_all_as_read(candidate_id)
            return {
                'success': True,
                'message': f'{count} پیام به عنوان خوانده شده علامت‌گذاری شد',
                'count': count
            }
        except Exception as e:
            logger.error(f"Error marking all as read: {e}")
            return {
                'success': False,
                'message': 'خطا در علامت‌گذاری پیام‌ها'
            }
    
    @staticmethod
    def get_dashboard_summary(candidate_id: int) -> Dict:
        """خلاصه پیام‌ها برای داشبورد"""
        try:
            stats = MessageRepository.get_statistics(candidate_id)
            recent = MessageRepository.get_by_candidate(candidate_id, limit=5, is_read=False)
            
            return {
                'success': True,
                'unread_count': stats.get('unread', 0),
                'today_count': stats.get('today', 0),
                'total_count': stats.get('total', 0),
                'avg_response_time': stats.get('avg_response_time', 0),
                'recent_messages': recent
            }
        except Exception as e:
            logger.error(f"Error getting dashboard summary: {e}")
            return {
                'success': False,
                'unread_count': 0,
                'today_count': 0,
                'total_count': 0
            }
    
    @staticmethod
    def send_reply(message_id: int, reply_text: str, candidate_id: int) -> Dict:
        """
        ارسال پاسخ به پیام (عملیات فرضی - نیاز به پیاده‌سازی کامل)
        
        Args:
            message_id: شناسه پیام
            reply_text: متن پاسخ
            candidate_id: شناسه کاندیدا
        
        Returns:
            dict با success و message
        """
        try:
            message = MessageRepository.get_by_id(message_id)
            if not message:
                return {
                    'success': False,
                    'message': 'پیام یافت نشد'
                }
            
            if message.candidate_id != candidate_id:
                return {
                    'success': False,
                    'message': 'شما مجاز به پاسخ این پیام نیستید'
                }
            
            # Mark as read
            MessageRepository.mark_as_read(message_id)
            
            # TODO: پیاده‌سازی ارسال پاسخ به bot user
            # از طریق Telegram Bot API
            
            logger.info(f"Reply sent for message {message_id}")
            return {
                'success': True,
                'message': 'پاسخ با موفقیت ارسال شد'
            }
            
        except Exception as e:
            logger.error(f"Error sending reply: {e}")
            return {
                'success': False,
                'message': 'خطا در ارسال پاسخ'
            }
