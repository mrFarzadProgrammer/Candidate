# -*- coding: utf-8 -*-
"""
VIP Citizen System Utilities
ماژول کمکی برای سیستم شهروند ماه و جلسات VIP
"""

from datetime import datetime, timedelta
from sqlalchemy import func, desc
from database.models import (
    db, Candidate, CitizenProfile, CitizenContribution, 
    ContributionVote, ContributionComment, MonthlyTopCitizen, VIPInteraction
)


def calculate_citizen_score(citizen_telegram_id, month=None, year=None):
    """
    محاسبه امتیاز شهروند برای انتخاب VIP
    فرمول: (مشارکت‌ها × 10) + (آپ‌ووت‌ها × 5) + (کامنت‌ها × 2)
    """
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year
    
    # تاریخ شروع و پایان ماه
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # تعداد مشارکت‌های ثبت شده
    contributions_count = CitizenContribution.query.filter(
        CitizenContribution.user_telegram_id == citizen_telegram_id,
        CitizenContribution.status == 'approved',
        CitizenContribution.created_at >= start_date,
        CitizenContribution.created_at < end_date
    ).count()
    
    # تعداد آپ‌ووت‌های دریافتی
    upvotes_count = db.session.query(func.count(ContributionVote.id)).join(
        CitizenContribution, ContributionVote.contribution_id == CitizenContribution.id
    ).filter(
        CitizenContribution.user_telegram_id == citizen_telegram_id,
        ContributionVote.vote_type == 'upvote',
        ContributionVote.voted_at >= start_date,
        ContributionVote.voted_at < end_date
    ).scalar() or 0
    
    # تعداد کامنت‌های گذاشته شده
    comments_count = ContributionComment.query.filter(
        ContributionComment.user_telegram_id == citizen_telegram_id,
        ContributionComment.created_at >= start_date,
        ContributionComment.created_at < end_date
    ).count()
    
    # محاسبه امتیاز نهایی
    score = (contributions_count * 10) + (upvotes_count * 5) + (comments_count * 2)
    
    return {
        'total_score': score,
        'contributions': contributions_count,
        'upvotes': upvotes_count,
        'comments': comments_count,
        'month': month,
        'year': year
    }


def select_monthly_top_citizens(candidate_id, month=None, year=None, limit=3):
    """
    انتخاب شهروندان برتر ماه (3 نفر اول)
    Returns: list of dicts with citizen info and scores
    """
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year
    
    # لیست تمام telegram_id های شهروندانی که برای این نامزد مشارکت داشتند
    citizen_telegram_ids = db.session.query(
        CitizenContribution.user_telegram_id
    ).filter_by(
        candidate_id=candidate_id
    ).distinct().all()
    
    if not citizen_telegram_ids:
        return []
    
    # محاسبه امتیاز برای همه
    citizen_scores = []
    for (telegram_id,) in citizen_telegram_ids:
        citizen = CitizenProfile.query.get(telegram_id)
        if not citizen:
            continue
            
        score_data = calculate_citizen_score(telegram_id, month, year)
        if score_data['total_score'] > 0:  # فقط افراد با امتیاز بیشتر از صفر
            citizen_scores.append({
                'citizen': citizen,
                'score_data': score_data
            })
    
    # مرتب‌سازی بر اساس امتیاز
    citizen_scores.sort(key=lambda x: x['score_data']['total_score'], reverse=True)
    
    # انتخاب 3 نفر اول
    top_citizens = citizen_scores[:limit]
    
    return top_citizens


def award_vip_status(candidate_id, month=None, year=None):
    """
    اعطای وضعیت VIP به 3 شهروند برتر
    رتبه 1: طلایی (gold)
    رتبه 2: نقره‌ای (silver)
    رتبه 3: برنزی (bronze)
    """
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year
    
    # چک کنیم که قبلاً برای این ماه اجرا نشده باشد
    existing = MonthlyTopCitizen.query.filter_by(
        candidate_id=candidate_id,
        month=month,
        year=year
    ).first()
    
    if existing:
        return {'success': False, 'message': 'این ماه قبلاً پردازش شده است'}
    
    # انتخاب برترین‌ها
    top_citizens = select_monthly_top_citizens(candidate_id, month, year, limit=3)
    
    if not top_citizens:
        return {'success': False, 'message': 'هیچ شهروند فعالی وجود ندارد'}
    
    # اعطای وضعیت VIP
    vip_statuses = ['gold', 'silver', 'bronze']
    awarded = []
    
    for rank, item in enumerate(top_citizens, 1):
        citizen = item['citizen']
        score_data = item['score_data']
        vip_status = vip_statuses[rank - 1] if rank <= 3 else None
        
        # ثبت در جدول MonthlyTopCitizen
        top_citizen = MonthlyTopCitizen(
            candidate_id=candidate_id,
            citizen_telegram_id=citizen.telegram_id,
            month=month,
            year=year,
            rank=rank,
            total_score=score_data['total_score'],
            contributions_count=score_data['contributions'],
            upvotes_count=score_data['upvotes'],
            comments_count=score_data['comments'],
            vip_status=vip_status,
            awarded_at=datetime.utcnow()
        )
        
        db.session.add(top_citizen)
        awarded.append({
            'rank': rank,
            'citizen_name': citizen.full_name,
            'score': score_data['total_score'],
            'vip_status': vip_status
        })
    
    db.session.commit()
    
    return {
        'success': True,
        'message': f'{len(awarded)} شهروند برتر انتخاب شدند',
        'awarded': awarded
    }


def get_vip_citizens(candidate_id, month=None, year=None):
    """
    دریافت لیست شهروندان VIP این ماه
    """
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year
    
    vips = db.session.query(MonthlyTopCitizen, CitizenProfile).join(
        CitizenProfile, MonthlyTopCitizen.citizen_telegram_id == CitizenProfile.telegram_id
    ).filter(
        MonthlyTopCitizen.candidate_id == candidate_id,
        MonthlyTopCitizen.month == month,
        MonthlyTopCitizen.year == year
    ).order_by(MonthlyTopCitizen.rank).all()
    
    result = []
    for top_citizen, citizen in vips:
        result.append({
            'rank': top_citizen.rank,
            'vip_status': top_citizen.vip_status,
            'citizen_name': citizen.full_name,
            'citizen_phone': citizen.phone,
            'telegram_id': citizen.telegram_id,
            'total_score': top_citizen.total_score,
            'contributions': top_citizen.contributions_count,
            'upvotes': top_citizen.upvotes_count,
            'comments': top_citizen.comments_count,
            'awarded_at': top_citizen.awarded_at
        })
    
    return result


def schedule_vip_interaction(candidate_id, citizen_telegram_id, interaction_type, 
                            scheduled_date, title, description=None,
                            meeting_platform=None, meeting_link=None):
    """
    زمان‌بندی جلسه VIP با شهروند برتر
    """
    interaction = VIPInteraction(
        candidate_id=candidate_id,
        citizen_telegram_id=citizen_telegram_id,
        interaction_type=interaction_type,
        title=title,
        description=description,
        scheduled_at=scheduled_date,
        meeting_link=meeting_link,
        status='scheduled'
    )
    
    db.session.add(interaction)
    db.session.commit()
    
    return interaction


def get_upcoming_vip_interactions(candidate_id, days_ahead=30):
    """
    دریافت جلسات VIP آینده
    """
    today = datetime.now()
    future_date = today + timedelta(days=days_ahead)
    
    interactions = db.session.query(VIPInteraction, CitizenProfile).join(
        CitizenProfile, VIPInteraction.citizen_telegram_id == CitizenProfile.telegram_id
    ).filter(
        VIPInteraction.candidate_id == candidate_id,
        VIPInteraction.scheduled_at >= today,
        VIPInteraction.scheduled_at <= future_date,
        VIPInteraction.status.in_(['scheduled', 'confirmed'])
    ).order_by(VIPInteraction.scheduled_at).all()
    
    result = []
    for interaction, citizen in interactions:
        result.append({
            'id': interaction.id,
            'interaction_type': interaction.interaction_type,
            'title': interaction.title,
            'description': interaction.description,
            'scheduled_date': interaction.scheduled_at,
            'meeting_platform': interaction.meeting_link.split('/')[2] if interaction.meeting_link else None,
            'meeting_link': interaction.meeting_link,
            'status': interaction.status,
            'citizen_name': citizen.full_name,
            'citizen_phone': citizen.phone,
            'telegram_id': citizen.telegram_id
        })
    
    return result


def complete_vip_interaction(interaction_id, notes=None):
    """
    تکمیل جلسه VIP
    """
    interaction = VIPInteraction.query.get(interaction_id)
    if not interaction:
        return False
    
    interaction.status = 'completed'
    interaction.completed_at = datetime.utcnow()
    if notes:
        interaction.notes = notes
    
    db.session.commit()
    return True


def cancel_vip_interaction(interaction_id, cancellation_reason=None):
    """
    لغو جلسه VIP
    """
    interaction = VIPInteraction.query.get(interaction_id)
    if not interaction:
        return False
    
    interaction.status = 'cancelled'
    if cancellation_reason:
        interaction.cancellation_reason = cancellation_reason
    
    db.session.commit()
    return True


def get_vip_statistics(candidate_id):
    """
    آمار کلی سیستم VIP
    """
    # تعداد کل شهروندان VIP تا کنون
    total_vips = MonthlyTopCitizen.query.filter_by(
        candidate_id=candidate_id
    ).count()
    
    # تعداد جلسات برگزار شده
    completed_interactions = VIPInteraction.query.filter_by(
        candidate_id=candidate_id,
        status='completed'
    ).count()
    
    # تعداد جلسات آینده
    upcoming_interactions = VIPInteraction.query.filter(
        VIPInteraction.candidate_id == candidate_id,
        VIPInteraction.scheduled_at >= datetime.now(),
        VIPInteraction.status.in_(['scheduled', 'confirmed'])
    ).count()
    
    # شهروند برتر این ماه
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    top_this_month = db.session.query(MonthlyTopCitizen, CitizenProfile).join(
        CitizenProfile, MonthlyTopCitizen.citizen_telegram_id == CitizenProfile.telegram_id
    ).filter(
        MonthlyTopCitizen.candidate_id == candidate_id,
        MonthlyTopCitizen.month == current_month,
        MonthlyTopCitizen.year == current_year,
        MonthlyTopCitizen.rank == 1
    ).first()
    
    top_citizen_name = top_this_month[1].full_name if top_this_month else None
    
    return {
        'total_vips': total_vips,
        'completed_interactions': completed_interactions,
        'upcoming_interactions': upcoming_interactions,
        'top_this_month': top_citizen_name
    }
