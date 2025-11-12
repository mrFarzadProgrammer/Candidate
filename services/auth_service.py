# -*- coding: utf-8 -*-
"""
Authentication Service
======================
سرویس مدیریت احراز هویت و لاگین/لاگ‌اوت
"""

from typing import Optional, Dict
from datetime import datetime
from repositories.candidate_repository import CandidateRepository
from security.security_utils import verify_password, hash_password
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """سرویس احراز هویت"""
    
    @staticmethod
    def login(username: str, password: str) -> Dict:
        """
        ورود کاربر
        
        Args:
            username: نام کاربری
            password: رمز عبور
        
        Returns:
            dict با success, message, candidate_id
        
        Example:
            result = AuthService.login('test', 'pass123')
            if result['success']:
                session['candidate_id'] = result['candidate_id']
        """
        try:
            # Validation
            if not username or not password:
                return {
                    'success': False,
                    'message': 'نام کاربری و رمز عبور الزامی است'
                }
            
            # Find candidate
            candidate = CandidateRepository.get_by_username(username)
            
            if not candidate:
                logger.warning(f"Login attempt for non-existent user: {username}")
                return {
                    'success': False,
                    'message': 'نام کاربری یا رمز عبور اشتباه است'
                }
            
            # Check active status
            if not candidate.is_active:
                logger.warning(f"Login attempt for inactive user: {username}")
                return {
                    'success': False,
                    'message': 'حساب کاربری شما غیرفعال است'
                }
            
            # Verify password
            if not verify_password(password, candidate.password):
                logger.warning(f"Failed login attempt for user: {username}")
                return {
                    'success': False,
                    'message': 'نام کاربری یا رمز عبور اشتباه است'
                }
            
            # Update last login
            CandidateRepository.update(candidate.id, last_login=datetime.now())
            
            logger.info(f"Successful login for user: {username}")
            return {
                'success': True,
                'message': 'ورود موفقیت‌آمیز',
                'candidate_id': candidate.id,
                'candidate': candidate
            }
            
        except Exception as e:
            logger.error(f"Error in login: {e}", exc_info=True)
            return {
                'success': False,
                'message': 'خطا در ورود به سیستم'
            }
    
    @staticmethod
    def change_password(candidate_id: int, old_password: str, new_password: str) -> Dict:
        """
        تغییر رمز عبور
        
        Args:
            candidate_id: شناسه کاندیدا
            old_password: رمز عبور فعلی
            new_password: رمز عبور جدید
        
        Returns:
            dict با success و message
        """
        try:
            # Validation
            if not old_password or not new_password:
                return {
                    'success': False,
                    'message': 'رمز عبور فعلی و جدید الزامی است'
                }
            
            if len(new_password) < 6:
                return {
                    'success': False,
                    'message': 'رمز عبور جدید باید حداقل 6 کاراکتر باشد'
                }
            
            # Get candidate
            candidate = CandidateRepository.get_by_id(candidate_id)
            if not candidate:
                return {
                    'success': False,
                    'message': 'کاربر یافت نشد'
                }
            
            # Verify old password
            if not verify_password(old_password, candidate.password):
                return {
                    'success': False,
                    'message': 'رمز عبور فعلی اشتباه است'
                }
            
            # Hash and update new password
            hashed_password = hash_password(new_password)
            if CandidateRepository.update(candidate_id, password=hashed_password):
                logger.info(f"Password changed for candidate {candidate_id}")
                return {
                    'success': True,
                    'message': 'رمز عبور با موفقیت تغییر کرد'
                }
            
            return {
                'success': False,
                'message': 'خطا در تغییر رمز عبور'
            }
            
        except Exception as e:
            logger.error(f"Error changing password: {e}", exc_info=True)
            return {
                'success': False,
                'message': 'خطا در تغییر رمز عبور'
            }
    
    @staticmethod
    def register(username: str, password: str, full_name: str, **kwargs) -> Dict:
        """
        ثبت‌نام کاربر جدید
        
        Args:
            username: نام کاربری
            password: رمز عبور
            full_name: نام کامل
            **kwargs: سایر فیلدها
        
        Returns:
            dict با success, message, candidate_id
        """
        try:
            # Validation
            if not username or not password or not full_name:
                return {
                    'success': False,
                    'message': 'تمام فیلدهای اجباری را پر کنید'
                }
            
            if len(password) < 6:
                return {
                    'success': False,
                    'message': 'رمز عبور باید حداقل 6 کاراکتر باشد'
                }
            
            # Check if username exists
            if CandidateRepository.exists(username=username):
                return {
                    'success': False,
                    'message': 'این نام کاربری قبلاً استفاده شده است'
                }
            
            # Hash password
            hashed_password = hash_password(password)
            
            # Create candidate
            candidate = CandidateRepository.create(
                username=username,
                password=hashed_password,
                full_name=full_name,
                **kwargs
            )
            
            if candidate:
                logger.info(f"New candidate registered: {username}")
                return {
                    'success': True,
                    'message': 'ثبت‌نام با موفقیت انجام شد',
                    'candidate_id': candidate.id
                }
            
            return {
                'success': False,
                'message': 'خطا در ثبت‌نام'
            }
            
        except Exception as e:
            logger.error(f"Error in registration: {e}", exc_info=True)
            return {
                'success': False,
                'message': 'خطا در ثبت‌نام'
            }
