# -*- coding: utf-8 -*-
"""
Referral Program Utilities
ماژول کمکی برای سیستم معرفی دوستان (Referral)
"""

import random
import string
from datetime import datetime
from sqlalchemy import func
from database.models import (
    db, Candidate, ReferralProgram, ReferralReward,
    PlanPurchase, Plan
)


def generate_referral_code(candidate_id, candidate_full_name):
    """
    تولید کد معرفی یونیک برای نامزد
    فرمت: نام + 4 رقم تصادفی (مثال: AHMAD1234)
    """
    # نام را به لاتین تبدیل کنیم (فقط حروف)
    base_name = ''.join(filter(str.isalpha, candidate_full_name.upper()))[:6]
    
    # اگر نام خالی بود از ID استفاده کن
    if not base_name:
        base_name = f"REF{candidate_id}"
    
    # تولید کد تا زمانی که یونیک باشد
    max_attempts = 10
    for _ in range(max_attempts):
        random_digits = ''.join(random.choices(string.digits, k=4))
        code = f"{base_name}{random_digits}"
        
        # چک کنیم که تکراری نباشد
        existing = ReferralProgram.query.filter_by(referral_code=code).first()
        if not existing:
            return code
    
    # اگر بعد از 10 بار هنوز یونیک نشد، از timestamp استفاده کن
    timestamp = str(int(datetime.now().timestamp()))[-6:]
    return f"{base_name}{timestamp}"


def create_referral_program(candidate_id):
    """
    ایجاد برنامه معرفی برای نامزد
    Returns: ReferralProgram object or None
    """
    # چک کنیم که قبلا نساخته باشیم
    existing = ReferralProgram.query.filter_by(
        candidate_id=candidate_id,
        status='active'
    ).first()
    
    if existing:
        return existing
    
    # اطلاعات نامزد
    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        return None
    
    # تولید کد معرفی
    referral_code = generate_referral_code(candidate_id, candidate.full_name)
    
    # ایجاد برنامه معرفی
    referral_program = ReferralProgram(
        candidate_id=candidate_id,
        referral_code=referral_code,
        status='active',
        total_referrals=0,
        successful_conversions=0,
        total_rewards_earned=0
    )
    
    db.session.add(referral_program)
    db.session.commit()
    
    return referral_program


def record_referral(referrer_code, new_candidate_id):
    """
    ثبت معرفی جدید
    Args:
        referrer_code: کد معرف
        new_candidate_id: ID نامزد جدید
    Returns: True if successful, False otherwise
    """
    # پیدا کردن برنامه معرفی
    referral_program = ReferralProgram.query.filter_by(
        referral_code=referrer_code,
        status='active'
    ).first()
    
    if not referral_program:
        return False
    
    # چک کنیم که خودش خودش رو معرفی نکرده باشه!
    if referral_program.candidate_id == new_candidate_id:
        return False
    
    # چک کنیم قبلا ثبت نشده باشه
    new_candidate = Candidate.query.get(new_candidate_id)
    if new_candidate and new_candidate.referred_by:
        return False  # قبلا معرفی شده
    
    # ثبت معرف در پروفایل نامزد جدید
    if new_candidate:
        new_candidate.referred_by = referral_program.candidate_id
        referral_program.total_referrals += 1
        db.session.commit()
        return True
    
    return False


def process_conversion_reward(converted_candidate_id):
    """
    پردازش پاداش معرفی وقتی کاربر معرفی شده پلن خرید
    Args:
        converted_candidate_id: ID نامزدی که پلن خرید
    Returns: ReferralReward object or None
    """
    # پیدا کردن نامزد
    candidate = Candidate.query.get(converted_candidate_id)
    if not candidate or not candidate.referred_by:
        return None
    
    # پیدا کردن برنامه معرفی معرف
    referral_program = ReferralProgram.query.filter_by(
        candidate_id=candidate.referred_by,
        status='active'
    ).first()
    
    if not referral_program:
        return None
    
    # چک کنیم که قبلا پاداش نگرفته باشه
    existing_reward = ReferralReward.query.filter_by(
        referral_program_id=referral_program.id,
        referred_candidate_id=converted_candidate_id
    ).first()
    
    if existing_reward:
        return existing_reward  # قبلا پاداش داده شده
    
    # پیدا کردن آخرین خرید
    latest_purchase = PlanPurchase.query.filter_by(
        candidate_id=converted_candidate_id
    ).order_by(PlanPurchase.start_date.desc()).first()
    
    if not latest_purchase:
        return None
    
    # محاسبه پاداش: 20% قیمت پلن خریداری شده
    reward_amount = latest_purchase.payment_amount * 0.20
    
    # ایجاد پاداش
    reward = ReferralReward(
        referral_program_id=referral_program.id,
        referred_candidate_id=converted_candidate_id,
        reward_type='plan_purchase',
        reward_amount=reward_amount,
        status='pending',
        awarded_at=datetime.utcnow()
    )
    
    db.session.add(reward)
    
    # آپدیت آمار معرف
    referral_program.successful_conversions += 1
    referral_program.total_rewards_earned += reward_amount
    
    db.session.commit()
    
    return reward


def approve_reward(reward_id):
    """
    تایید و پرداخت پاداش معرفی
    Args:
        reward_id: ID پاداش
    Returns: True if successful, False otherwise
    """
    reward = ReferralReward.query.get(reward_id)
    if not reward or reward.status != 'pending':
        return False
    
    reward.status = 'approved'
    reward.approved_at = datetime.utcnow()
    db.session.commit()
    
    return True


def get_referral_stats(candidate_id):
    """
    آمار معرفی‌های نامزد
    Returns: dict with stats
    """
    referral_program = ReferralProgram.query.filter_by(
        candidate_id=candidate_id,
        status='active'
    ).first()
    
    if not referral_program:
        return {
            'has_program': False,
            'referral_code': None,
            'total_referrals': 0,
            'successful_conversions': 0,
            'pending_rewards': 0,
            'approved_rewards': 0,
            'total_earned': 0,
            'conversion_rate': 0,
            'top_referrals': []
        }
    
    # پاداش‌های در انتظار و تایید شده
    pending_rewards = ReferralReward.query.filter_by(
        referral_program_id=referral_program.id,
        status='pending'
    ).count()
    
    approved_rewards = ReferralReward.query.filter_by(
        referral_program_id=referral_program.id,
        status='approved'
    ).count()
    
    total_earned = db.session.query(func.sum(ReferralReward.reward_amount)).filter(
        ReferralReward.referral_program_id == referral_program.id,
        ReferralReward.status == 'approved'
    ).scalar() or 0
    
    # نرخ تبدیل
    conversion_rate = 0
    if referral_program.total_referrals > 0:
        conversion_rate = (referral_program.successful_conversions / 
                          referral_program.total_referrals * 100)
    
    # لیست افراد معرفی شده
    referred_candidates = Candidate.query.filter_by(
        referred_by=candidate_id
    ).order_by(Candidate.created_at.desc()).limit(10).all()
    
    top_referrals = []
    for ref in referred_candidates:
        # چک کنیم پلن خریده یا نه
        has_plan = PlanPurchase.query.filter_by(
            candidate_id=ref.id,
            is_active=True
        ).first() is not None
        
        # پاداش این معرفی
        reward = ReferralReward.query.filter_by(
            referral_program_id=referral_program.id,
            referred_candidate_id=ref.id
        ).first()
        
        top_referrals.append({
            'name': ref.full_name,
            'phone': ref.phone,
            'created_at': ref.created_at,
            'has_plan': has_plan,
            'reward_amount': reward.reward_amount if reward else 0,
            'reward_status': reward.status if reward else 'no_purchase'
        })
    
    return {
        'has_program': True,
        'referral_code': referral_program.referral_code,
        'total_referrals': referral_program.total_referrals,
        'successful_conversions': referral_program.successful_conversions,
        'pending_rewards': pending_rewards,
        'approved_rewards': approved_rewards,
        'total_earned': total_earned,
        'conversion_rate': round(conversion_rate, 1),
        'top_referrals': top_referrals
    }


def get_leaderboard(limit=10):
    """
    لیدربورد برترین معرفین
    Args:
        limit: تعداد نفرات برتر
    Returns: list of dicts
    """
    top_referrers = ReferralProgram.query.filter_by(
        status='active'
    ).order_by(
        ReferralProgram.successful_conversions.desc()
    ).limit(limit).all()
    
    leaderboard = []
    for idx, program in enumerate(top_referrers, 1):
        candidate = Candidate.query.get(program.candidate_id)
        if candidate:
            leaderboard.append({
                'rank': idx,
                'name': candidate.full_name,
                'referral_code': program.referral_code,
                'total_referrals': program.total_referrals,
                'successful_conversions': program.successful_conversions,
                'total_earned': program.total_rewards_earned,
                'conversion_rate': round(
                    (program.successful_conversions / program.total_referrals * 100)
                    if program.total_referrals > 0 else 0,
                    1
                )
            })
    
    return leaderboard
