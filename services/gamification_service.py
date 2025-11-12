# -*- coding: utf-8 -*-
"""
Gamification Service
====================
سیستم امتیازدهی و گیمیفیکیشن

امکانات:
- اعطای امتیاز برای اکشن‌ها
- محاسبه سطح کاربر
- مدیریت streak (حضور پیاپی)
- اعطای badge
- جدول برترین‌ها
"""

from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)

# سطوح (Levels) و امتیازات مورد نیاز
LEVELS = [
    {'level': 1, 'min_points': 0, 'name': 'شهروند فعال', 'emoji': '🥉'},
    {'level': 2, 'min_points': 500, 'name': 'حامی', 'emoji': '🥈'},
    {'level': 3, 'min_points': 2000, 'name': 'سفیر', 'emoji': '🥇'},
    {'level': 4, 'min_points': 5000, 'name': 'VIP', 'emoji': '💎'},
    {'level': 5, 'min_points': 10000, 'name': 'افسانه', 'emoji': '👑'},
]

# اکشن‌ها و امتیازات
DEFAULT_ACTIONS = {
    'join': {'points': 100, 'name': 'عضویت در ربات', 'badge': 'welcome'},
    'message': {'points': 10, 'name': 'ارسال پیام', 'repeatable': True},
    'referral': {'points': 50, 'name': 'دعوت دوست', 'badge': 'networker'},
    'poll_vote': {'points': 25, 'name': 'شرکت در نظرسنجی', 'badge': 'voter'},
    'daily_login': {'points': 5, 'name': 'حضور روزانه', 'streak_bonus': True},
    'share_post': {'points': 15, 'name': 'اشتراک‌گذاری', 'badge': 'promoter'},
    'contribution': {'points': 30, 'name': 'ارسال ایده', 'badge': 'thinker'},
    'comment': {'points': 5, 'name': 'نظر دادن', 'repeatable': True},
}

# Badge‌ها
DEFAULT_BADGES = {
    'welcome': {'name': 'خوش آمدید', 'emoji': '👋', 'condition': 'join'},
    'networker': {'name': 'شبکه‌ساز', 'emoji': '🌐', 'condition': 'referral >= 10'},
    'active': {'name': 'فعال', 'emoji': '⚡', 'condition': 'streak >= 7'},
    'super_active': {'name': 'فوق فعال', 'emoji': '🔥', 'condition': 'streak >= 30'},
    'voter': {'name': 'رای‌دهنده', 'emoji': '🗳️', 'condition': 'poll_votes >= 5'},
    'promoter': {'name': 'تبلیغ‌کننده', 'emoji': '📢', 'condition': 'shares >= 10'},
    'thinker': {'name': 'متفکر', 'emoji': '💡', 'condition': 'contributions >= 5'},
    'vip': {'name': 'VIP', 'emoji': '👑', 'condition': 'level >= 4'},
}


class GamificationService:
    """سرویس اصلی گیمیفیکیشن"""
    
    @staticmethod
    def award_points(bot_user, action_code: str, reference_id: int = None, 
                     reference_type: str = None, bonus: int = 0) -> Dict:
        """
        اعطای امتیاز به کاربر
        
        Args:
            bot_user: شیء BotUser
            action_code: کد اکشن (join, message, referral, etc.)
            reference_id: ID مرتبط
            reference_type: نوع مرجع
            bonus: امتیاز اضافی
        
        Returns:
            dict با نتیجه و اطلاعات
        """
        from database.models import db, UserPoints, GamificationAction
        
        try:
            # دریافت اکشن
            action = GamificationAction.query.filter_by(code=action_code, is_active=True).first()
            
            if not action:
                # fallback به default
                if action_code in DEFAULT_ACTIONS:
                    points = DEFAULT_ACTIONS[action_code]['points']
                    name = DEFAULT_ACTIONS[action_code]['name']
                else:
                    return {'success': False, 'message': 'اکشن یافت نشد'}
            else:
                points = action.points
                name = action.name
            
            # محاسبه streak bonus
            if action_code == 'daily_login':
                streak_bonus = GamificationService._calculate_daily_login(bot_user)
                bonus += streak_bonus
            
            total_points = points + bonus
            
            # ثبت تاریخچه
            user_point = UserPoints(
                bot_user_id=bot_user.id,
                action_code=action_code,
                points=total_points,
                description=name,
                reference_id=reference_id,
                reference_type=reference_type
            )
            db.session.add(user_point)
            
            # آپدیت امتیاز کل کاربر
            old_level = GamificationService.get_user_level(bot_user.total_points)
            bot_user.total_points += total_points
            new_level_data = GamificationService.get_user_level(bot_user.total_points)
            bot_user.level = new_level_data['level']
            
            db.session.commit()
            
            # بررسی level up
            level_up = new_level_data['level'] > old_level['level']
            
            # بررسی badge جدید
            new_badges = []
            if action_code in DEFAULT_ACTIONS and 'badge' in DEFAULT_ACTIONS[action_code]:
                badge_code = DEFAULT_ACTIONS[action_code]['badge']
                if GamificationService._check_and_award_badge(bot_user, badge_code):
                    new_badges.append(badge_code)
            
            return {
                'success': True,
                'points_awarded': total_points,
                'total_points': bot_user.total_points,
                'level': new_level_data,
                'level_up': level_up,
                'new_badges': new_badges
            }
            
        except Exception as e:
            logger.error(f"Error awarding points: {e}")
            db.session.rollback()
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def _calculate_daily_login(bot_user) -> int:
        """محاسبه streak و bonus روزانه"""
        from database.models import db
        
        today = date.today()
        
        # اگر اولین بار است
        if not bot_user.last_daily_login:
            bot_user.last_daily_login = today
            bot_user.streak_days = 1
            return 0
        
        # اگر امروز قبلاً لاگین کرده
        if bot_user.last_daily_login == today:
            return 0
        
        # اگر دیروز لاگین کرده (ادامه streak)
        yesterday = today - timedelta(days=1)
        if bot_user.last_daily_login == yesterday:
            bot_user.streak_days += 1
            bot_user.last_daily_login = today
            
            # bonus بر اساس streak
            streak_bonus = bot_user.streak_days * 2  # هر روز 2 امتیاز بیشتر
            
            # بررسی badge streak
            if bot_user.streak_days == 7:
                GamificationService._check_and_award_badge(bot_user, 'active')
            elif bot_user.streak_days == 30:
                GamificationService._check_and_award_badge(bot_user, 'super_active')
            
            return streak_bonus
        
        # اگر streak شکسته شده
        else:
            bot_user.streak_days = 1
            bot_user.last_daily_login = today
            return 0
    
    @staticmethod
    def get_user_level(points: int) -> Dict:
        """محاسبه سطح کاربر بر اساس امتیاز"""
        for i, level in enumerate(reversed(LEVELS)):
            if points >= level['min_points']:
                # محاسبه پیشرفت تا سطح بعدی
                current_level = level
                if i > 0:
                    next_level = LEVELS[len(LEVELS) - i]
                    points_to_next = next_level['min_points'] - points
                    progress = ((points - current_level['min_points']) / 
                               (next_level['min_points'] - current_level['min_points']) * 100)
                else:
                    points_to_next = 0
                    progress = 100
                
                return {
                    'level': current_level['level'],
                    'name': current_level['name'],
                    'emoji': current_level['emoji'],
                    'min_points': current_level['min_points'],
                    'points_to_next': points_to_next,
                    'progress': round(progress, 1)
                }
        
        return LEVELS[0]
    
    @staticmethod
    def _check_and_award_badge(bot_user, badge_code: str) -> bool:
        """بررسی و اعطای badge"""
        from database.models import db, Badge, UserBadge
        
        try:
            # پیدا کردن badge
            badge = Badge.query.filter_by(code=badge_code, is_active=True).first()
            if not badge:
                return False
            
            # بررسی آیا قبلاً گرفته
            existing = UserBadge.query.filter_by(
                bot_user_id=bot_user.id,
                badge_id=badge.id
            ).first()
            
            if existing:
                return False
            
            # اعطا
            user_badge = UserBadge(
                bot_user_id=bot_user.id,
                badge_id=badge.id
            )
            db.session.add(user_badge)
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error awarding badge: {e}")
            return False
    
    @staticmethod
    def get_leaderboard(bot_instance_id: int, limit: int = 10) -> List[Dict]:
        """دریافت جدول برترین‌ها"""
        from database.models import BotUser
        
        try:
            top_users = BotUser.query.filter_by(bot_instance_id=bot_instance_id)\
                .order_by(BotUser.total_points.desc())\
                .limit(limit).all()
            
            leaderboard = []
            for i, user in enumerate(top_users, 1):
                level_data = GamificationService.get_user_level(user.total_points)
                leaderboard.append({
                    'rank': i,
                    'name': f"{user.first_name} {user.last_name or ''}".strip(),
                    'username': user.username,
                    'points': user.total_points,
                    'level': level_data['level'],
                    'level_name': level_data['name'],
                    'level_emoji': level_data['emoji'],
                    'streak': user.streak_days
                })
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    @staticmethod
    def get_user_stats(bot_user) -> Dict:
        """آمار کامل کاربر"""
        from database.models import UserBadge, Badge
        
        try:
            level_data = GamificationService.get_user_level(bot_user.total_points)
            
            # badge‌های کاربر
            user_badges = UserBadge.query.filter_by(bot_user_id=bot_user.id).all()
            badges = []
            for ub in user_badges:
                badge = Badge.query.get(ub.badge_id)
                if badge:
                    badges.append({
                        'code': badge.code,
                        'name': badge.name,
                        'emoji': badge.emoji,
                        'earned_at': ub.earned_at.strftime('%Y/%m/%d')
                    })
            
            return {
                'total_points': bot_user.total_points,
                'level': level_data,
                'streak_days': bot_user.streak_days,
                'badges': badges,
                'badges_count': len(badges)
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
    
    @staticmethod
    def initialize_default_actions():
        """ایجاد اکشن‌های پیش‌فرض"""
        from database.models import db, GamificationAction
        
        for code, data in DEFAULT_ACTIONS.items():
            existing = GamificationAction.query.filter_by(code=code).first()
            if not existing:
                action = GamificationAction(
                    code=code,
                    name=data['name'],
                    points=data['points'],
                    is_repeatable=data.get('repeatable', False),
                    counts_for_streak=data.get('streak_bonus', False)
                )
                db.session.add(action)
        
        db.session.commit()
        logger.info("Default gamification actions initialized")
    
    @staticmethod
    def initialize_default_badges():
        """ایجاد badge‌های پیش‌فرض"""
        from database.models import db, Badge
        
        for code, data in DEFAULT_BADGES.items():
            existing = Badge.query.filter_by(code=code).first()
            if not existing:
                badge = Badge(
                    code=code,
                    name=data['name'],
                    emoji=data['emoji'],
                    description=f"دریافت این نشان با {data['condition']}"
                )
                db.session.add(badge)
        
        db.session.commit()
        logger.info("Default badges initialized")


# تست
if __name__ == "__main__":
    print("🎮 تست سیستم Gamification\n")
    
    # تست محاسبه سطح
    test_points = [0, 500, 2000, 5000, 10000]
    for points in test_points:
        level = GamificationService.get_user_level(points)
        print(f"امتیاز {points}: {level['emoji']} {level['name']} (سطح {level['level']})")
        if level['points_to_next'] > 0:
            print(f"   تا سطح بعدی: {level['points_to_next']} امتیاز ({level['progress']}%)")
        print()
