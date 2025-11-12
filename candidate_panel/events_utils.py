#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
توابع کمکی مدیریت رویدادهای زنده
=====================================

این ماژول شامل توابع برای:
- ایجاد و مدیریت رویدادهای زنده
- ثبت‌نام و مدیریت شرکت‌کنندگان
- مدیریت سوالات و پاسخ‌ها
- ارسال یادآوری‌ها
- آمارگیری از رویدادها
"""

from datetime import datetime, timedelta
from database.models import db, LiveEvent, EventRegistration, EventQuestion, Candidate, BotUser
from sqlalchemy import and_, or_, func


# ═══════════════════════════════════════════════════════════════
# بخش اول: مدیریت رویدادها
# ═══════════════════════════════════════════════════════════════

def create_event(candidate_id, title, description, event_type, starts_at,
                duration_minutes=60, platform='telegram_live', stream_url=None,
                max_participants=None, vip_only=False, min_points_required=0,
                requires_registration=True, banner_image=None):
    """
    ایجاد رویداد جدید
    
    Args:
        candidate_id: شناسه نماینده
        title: عنوان رویداد
        description: توضیحات
        event_type: نوع رویداد (live_qa, town_hall, webinar, ama, workshop)
        starts_at: زمان شروع (datetime)
        duration_minutes: مدت زمان (دقیقه)
        platform: پلتفرم (telegram_live, zoom, youtube_live, instagram_live)
        stream_url: لینک پخش
        max_participants: حداکثر شرکت‌کننده (None = نامحدود)
        vip_only: فقط برای VIP
        min_points_required: حداقل امتیاز لازم
        requires_registration: نیاز به ثبت‌نام
        banner_image: تصویر بنر
    
    Returns:
        LiveEvent object
    """
    event = LiveEvent(
        candidate_id=candidate_id,
        title=title,
        description=description,
        event_type=event_type,
        starts_at=starts_at,
        duration_minutes=duration_minutes,
        platform=platform,
        stream_url=stream_url,
        max_participants=max_participants,
        vip_only=vip_only,
        min_points_required=min_points_required,
        requires_registration=requires_registration,
        banner_image=banner_image,
        status='scheduled'
    )
    
    db.session.add(event)
    db.session.commit()
    
    return event


def update_event(event_id, **kwargs):
    """
    به‌روزرسانی رویداد
    
    Args:
        event_id: شناسه رویداد
        **kwargs: فیلدهای قابل به‌روزرسانی
    
    Returns:
        LiveEvent object یا None
    """
    event = LiveEvent.query.get(event_id)
    if not event:
        return None
    
    allowed_fields = [
        'title', 'description', 'starts_at', 'duration_minutes', 'platform',
        'stream_url', 'max_participants', 'vip_only', 'min_points_required',
        'requires_registration', 'banner_image', 'status', 'chat_enabled'
    ]
    
    for key, value in kwargs.items():
        if key in allowed_fields:
            setattr(event, key, value)
    
    db.session.commit()
    return event


def cancel_event(event_id, reason=None):
    """
    لغو رویداد
    
    Args:
        event_id: شناسه رویداد
        reason: دلیل لغو
    
    Returns:
        bool
    """
    event = LiveEvent.query.get(event_id)
    if not event:
        return False
    
    event.status = 'cancelled'
    db.session.commit()
    
    # TODO: ارسال اطلاع‌رسانی لغو به ثبت‌نام‌کنندگان
    
    return True


def start_event(event_id):
    """
    شروع رویداد (تغییر وضعیت به live)
    
    Args:
        event_id: شناسه رویداد
    
    Returns:
        bool
    """
    event = LiveEvent.query.get(event_id)
    if not event:
        return False
    
    event.status = 'live'
    db.session.commit()
    
    # TODO: ارسال اطلاع‌رسانی شروع به شرکت‌کنندگان
    
    return True


def complete_event(event_id):
    """
    پایان رویداد
    
    Args:
        event_id: شناسه رویداد
    
    Returns:
        bool
    """
    event = LiveEvent.query.get(event_id)
    if not event:
        return False
    
    event.status = 'completed'
    
    # محاسبه تعداد حضور
    event.attended_count = EventRegistration.query.filter_by(
        event_id=event_id,
        attended=True
    ).count()
    
    # محاسبه میانگین رتبه
    ratings = db.session.query(func.avg(EventRegistration.rating)).filter(
        EventRegistration.event_id == event_id,
        EventRegistration.rating.isnot(None)
    ).scalar()
    
    event.avg_rating = float(ratings) if ratings else 0
    
    db.session.commit()
    
    return True


def get_candidate_events(candidate_id, status=None, upcoming_only=False):
    """
    دریافت لیست رویدادهای نماینده
    
    Args:
        candidate_id: شناسه نماینده
        status: فیلتر براساس وضعیت (scheduled, live, completed, cancelled)
        upcoming_only: فقط رویدادهای آینده
    
    Returns:
        list of LiveEvent
    """
    query = LiveEvent.query.filter_by(candidate_id=candidate_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if upcoming_only:
        query = query.filter(LiveEvent.starts_at > datetime.utcnow())
    
    return query.order_by(LiveEvent.starts_at.desc()).all()


def get_event_details(event_id):
    """
    دریافت جزئیات کامل رویداد
    
    Args:
        event_id: شناسه رویداد
    
    Returns:
        dict با جزئیات کامل
    """
    event = LiveEvent.query.get(event_id)
    if not event:
        return None
    
    return {
        'id': event.id,
        'title': event.title,
        'description': event.description,
        'type': event.event_type,
        'starts_at': event.starts_at.isoformat(),
        'duration_minutes': event.duration_minutes,
        'platform': event.platform,
        'stream_url': event.stream_url,
        'status': event.status,
        'registered_count': event.registered_count,
        'attended_count': event.attended_count,
        'questions_count': event.questions_count,
        'avg_rating': event.avg_rating,
        'max_participants': event.max_participants,
        'vip_only': event.vip_only,
        'min_points_required': event.min_points_required,
        'requires_registration': event.requires_registration,
        'banner_image': event.banner_image,
        'candidate': {
            'id': event.candidate.id,
            'name': event.candidate.full_name
        }
    }


# ═══════════════════════════════════════════════════════════════
# بخش دوم: مدیریت ثبت‌نام و شرکت‌کنندگان
# ═══════════════════════════════════════════════════════════════

def register_for_event(event_id, citizen_telegram_id, full_name=None, phone=None, submitted_question=None):
    """
    ثبت‌نام در رویداد
    
    Args:
        event_id: شناسه رویداد
        citizen_telegram_id: شناسه تلگرام شهروند
        full_name: نام کامل
        phone: شماره تلفن
        submitted_question: سوال ارسالی (اختیاری)
    
    Returns:
        tuple (success: bool, message: str, registration: EventRegistration)
    """
    event = LiveEvent.query.get(event_id)
    if not event:
        return False, "رویداد یافت نشد", None
    
    # بررسی وضعیت رویداد
    if event.status == 'cancelled':
        return False, "این رویداد لغو شده است", None
    
    if event.status == 'completed':
        return False, "این رویداد به پایان رسیده است", None
    
    # بررسی ثبت‌نام قبلی
    existing = EventRegistration.query.filter_by(
        event_id=event_id,
        citizen_telegram_id=citizen_telegram_id
    ).first()
    
    if existing:
        return False, "شما قبلاً در این رویداد ثبت‌نام کرده‌اید", existing
    
    # بررسی ظرفیت
    if event.max_participants and event.registered_count >= event.max_participants:
        return False, "ظرفیت رویداد تکمیل شده است", None
    
    # بررسی محدودیت VIP
    if event.vip_only:
        # TODO: بررسی وضعیت VIP کاربر
        pass
    
    # بررسی محدودیت امتیاز
    if event.min_points_required > 0:
        # TODO: بررسی امتیاز کاربر
        pass
    
    # ثبت‌نام
    registration = EventRegistration(
        event_id=event_id,
        citizen_telegram_id=citizen_telegram_id,
        full_name=full_name,
        phone=phone,
        submitted_question=submitted_question
    )
    
    db.session.add(registration)
    
    # به‌روزرسانی شمارنده
    event.registered_count = event.registered_count + 1
    
    db.session.commit()
    
    return True, "ثبت‌نام شما با موفقیت انجام شد", registration


def cancel_registration(event_id, citizen_telegram_id):
    """
    لغو ثبت‌نام
    
    Args:
        event_id: شناسه رویداد
        citizen_telegram_id: شناسه تلگرام
    
    Returns:
        bool
    """
    registration = EventRegistration.query.filter_by(
        event_id=event_id,
        citizen_telegram_id=citizen_telegram_id
    ).first()
    
    if not registration:
        return False
    
    event = LiveEvent.query.get(event_id)
    if event:
        event.registered_count = max(0, event.registered_count - 1)
    
    db.session.delete(registration)
    db.session.commit()
    
    return True


def mark_attendance(event_id, citizen_telegram_id):
    """
    ثبت حضور در رویداد
    
    Args:
        event_id: شناسه رویداد
        citizen_telegram_id: شناسه تلگرام
    
    Returns:
        bool
    """
    registration = EventRegistration.query.filter_by(
        event_id=event_id,
        citizen_telegram_id=citizen_telegram_id
    ).first()
    
    if not registration:
        return False
    
    registration.attended = True
    registration.attended_at = datetime.utcnow()
    
    db.session.commit()
    
    return True


def submit_event_rating(event_id, citizen_telegram_id, rating, feedback=None):
    """
    ثبت رتبه و بازخورد
    
    Args:
        event_id: شناسه رویداد
        citizen_telegram_id: شناسه تلگرام
        rating: رتبه (1-5)
        feedback: بازخورد متنی
    
    Returns:
        bool
    """
    registration = EventRegistration.query.filter_by(
        event_id=event_id,
        citizen_telegram_id=citizen_telegram_id
    ).first()
    
    if not registration:
        return False
    
    registration.rating = rating
    registration.feedback = feedback
    
    db.session.commit()
    
    return True


def get_event_registrations(event_id, attended_only=False):
    """
    دریافت لیست ثبت‌نام‌کنندگان
    
    Args:
        event_id: شناسه رویداد
        attended_only: فقط حاضران
    
    Returns:
        list of EventRegistration
    """
    query = EventRegistration.query.filter_by(event_id=event_id)
    
    if attended_only:
        query = query.filter_by(attended=True)
    
    return query.order_by(EventRegistration.registered_at).all()


def get_citizen_registrations(citizen_telegram_id):
    """
    دریافت رویدادهای ثبت‌نام شده توسط شهروند
    
    Args:
        citizen_telegram_id: شناسه تلگرام
    
    Returns:
        list of dicts با جزئیات رویداد و ثبت‌نام
    """
    registrations = EventRegistration.query.filter_by(
        citizen_telegram_id=citizen_telegram_id
    ).all()
    
    result = []
    for reg in registrations:
        event = LiveEvent.query.get(reg.event_id)
        if event:
            result.append({
                'registration_id': reg.id,
                'event': {
                    'id': event.id,
                    'title': event.title,
                    'type': event.event_type,
                    'starts_at': event.starts_at.isoformat(),
                    'status': event.status,
                    'platform': event.platform
                },
                'registered_at': reg.registered_at.isoformat(),
                'attended': reg.attended,
                'rating': reg.rating
            })
    
    return result


# ═══════════════════════════════════════════════════════════════
# بخش سوم: مدیریت سوالات
# ═══════════════════════════════════════════════════════════════

def submit_question(event_id, citizen_telegram_id, citizen_name, question_text, category=None):
    """
    ارسال سوال
    
    Args:
        event_id: شناسه رویداد
        citizen_telegram_id: شناسه تلگرام
        citizen_name: نام شهروند
        question_text: متن سوال
        category: دسته‌بندی
    
    Returns:
        EventQuestion object
    """
    question = EventQuestion(
        event_id=event_id,
        citizen_telegram_id=citizen_telegram_id,
        citizen_name=citizen_name,
        question_text=question_text,
        question_category=category,
        status='pending'
    )
    
    db.session.add(question)
    
    # به‌روزرسانی شمارنده سوالات
    event = LiveEvent.query.get(event_id)
    if event:
        event.questions_count = event.questions_count + 1
    
    db.session.commit()
    
    return question


def approve_question(question_id):
    """
    تایید سوال برای نمایش
    
    Args:
        question_id: شناسه سوال
    
    Returns:
        bool
    """
    question = EventQuestion.query.get(question_id)
    if not question:
        return False
    
    question.status = 'approved'
    db.session.commit()
    
    return True


def answer_question(question_id, answer_text, answered_by):
    """
    پاسخ به سوال
    
    Args:
        question_id: شناسه سوال
        answer_text: متن پاسخ
        answered_by: نام پاسخ‌دهنده
    
    Returns:
        bool
    """
    question = EventQuestion.query.get(question_id)
    if not question:
        return False
    
    question.answer_text = answer_text
    question.answered_by = answered_by
    question.answered_at = datetime.utcnow()
    question.status = 'answered'
    
    db.session.commit()
    
    return True


def reject_question(question_id):
    """
    رد سوال
    
    Args:
        question_id: شناسه سوال
    
    Returns:
        bool
    """
    question = EventQuestion.query.get(question_id)
    if not question:
        return False
    
    question.status = 'rejected'
    db.session.commit()
    
    return True


def upvote_question(question_id):
    """
    رای مثبت به سوال
    
    Args:
        question_id: شناسه سوال
    
    Returns:
        int: تعداد رای جدید
    """
    question = EventQuestion.query.get(question_id)
    if not question:
        return 0
    
    question.upvotes = question.upvotes + 1
    db.session.commit()
    
    return question.upvotes


def get_event_questions(event_id, status=None, sort_by='created_at'):
    """
    دریافت سوالات رویداد
    
    Args:
        event_id: شناسه رویداد
        status: فیلتر براساس وضعیت (pending, approved, answered, rejected)
        sort_by: مرتب‌سازی (created_at, upvotes, priority)
    
    Returns:
        list of EventQuestion
    """
    query = EventQuestion.query.filter_by(event_id=event_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if sort_by == 'upvotes':
        query = query.order_by(EventQuestion.upvotes.desc())
    elif sort_by == 'priority':
        query = query.order_by(EventQuestion.priority.desc(), EventQuestion.upvotes.desc())
    else:
        query = query.order_by(EventQuestion.created_at.desc())
    
    return query.all()


# ═══════════════════════════════════════════════════════════════
# بخش چهارم: یادآوری‌ها و اطلاع‌رسانی
# ═══════════════════════════════════════════════════════════════

def send_reminders():
    """
    ارسال یادآوری‌های خودکار
    این تابع باید توسط Cron Job یا Celery Beat اجرا شود
    
    Returns:
        dict با آمار ارسال
    """
    now = datetime.utcnow()
    stats = {
        '1day': 0,
        '1hour': 0,
        'starting': 0
    }
    
    # یادآوری 1 روز قبل
    one_day_later = now + timedelta(days=1)
    events_1day = LiveEvent.query.filter(
        LiveEvent.status == 'scheduled',
        LiveEvent.reminder_1day_sent == False,
        LiveEvent.starts_at.between(one_day_later, one_day_later + timedelta(minutes=10))
    ).all()
    
    for event in events_1day:
        # TODO: ارسال پیام به ثبت‌نام‌کنندگان
        event.reminder_1day_sent = True
        stats['1day'] += 1
    
    # یادآوری 1 ساعت قبل
    one_hour_later = now + timedelta(hours=1)
    events_1hour = LiveEvent.query.filter(
        LiveEvent.status == 'scheduled',
        LiveEvent.reminder_1hour_sent == False,
        LiveEvent.starts_at.between(one_hour_later, one_hour_later + timedelta(minutes=5))
    ).all()
    
    for event in events_1hour:
        # TODO: ارسال پیام به ثبت‌نام‌کنندگان
        event.reminder_1hour_sent = True
        stats['1hour'] += 1
    
    # اطلاع شروع
    events_starting = LiveEvent.query.filter(
        LiveEvent.status == 'scheduled',
        LiveEvent.starting_notice_sent == False,
        LiveEvent.starts_at <= now
    ).all()
    
    for event in events_starting:
        # TODO: ارسال پیام شروع
        event.starting_notice_sent = True
        event.status = 'live'  # تغییر وضعیت به live
        stats['starting'] += 1
    
    db.session.commit()
    
    return stats


# ═══════════════════════════════════════════════════════════════
# بخش پنجم: آمار و گزارش
# ═══════════════════════════════════════════════════════════════

def get_event_statistics(event_id):
    """
    دریافت آمار کامل رویداد
    
    Args:
        event_id: شناسه رویداد
    
    Returns:
        dict با آمار کامل
    """
    event = LiveEvent.query.get(event_id)
    if not event:
        return None
    
    registrations = EventRegistration.query.filter_by(event_id=event_id).all()
    questions = EventQuestion.query.filter_by(event_id=event_id).all()
    
    # آمار ثبت‌نام
    registered_count = len(registrations)
    attended_count = sum(1 for r in registrations if r.attended)
    attendance_rate = (attended_count / registered_count * 100) if registered_count > 0 else 0
    
    # آمار رتبه‌دهی
    ratings = [r.rating for r in registrations if r.rating]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    rating_distribution = {
        '5': sum(1 for r in ratings if r == 5),
        '4': sum(1 for r in ratings if r == 4),
        '3': sum(1 for r in ratings if r == 3),
        '2': sum(1 for r in ratings if r == 2),
        '1': sum(1 for r in ratings if r == 1)
    }
    
    # آمار سوالات
    questions_by_status = {
        'pending': sum(1 for q in questions if q.status == 'pending'),
        'approved': sum(1 for q in questions if q.status == 'approved'),
        'answered': sum(1 for q in questions if q.status == 'answered'),
        'rejected': sum(1 for q in questions if q.status == 'rejected')
    }
    
    return {
        'event': {
            'id': event.id,
            'title': event.title,
            'type': event.event_type,
            'status': event.status,
            'starts_at': event.starts_at.isoformat(),
            'duration_minutes': event.duration_minutes
        },
        'registration': {
            'registered': registered_count,
            'attended': attended_count,
            'attendance_rate': round(attendance_rate, 2)
        },
        'rating': {
            'average': round(avg_rating, 2),
            'total_ratings': len(ratings),
            'distribution': rating_distribution
        },
        'questions': {
            'total': len(questions),
            'by_status': questions_by_status,
            'most_upvoted': max(questions, key=lambda q: q.upvotes) if questions else None
        }
    }


def get_candidate_events_summary(candidate_id):
    """
    خلاصه آمار رویدادهای نماینده
    
    Args:
        candidate_id: شناسه نماینده
    
    Returns:
        dict با خلاصه آمار
    """
    events = LiveEvent.query.filter_by(candidate_id=candidate_id).all()
    
    total_events = len(events)
    by_status = {
        'scheduled': sum(1 for e in events if e.status == 'scheduled'),
        'live': sum(1 for e in events if e.status == 'live'),
        'completed': sum(1 for e in events if e.status == 'completed'),
        'cancelled': sum(1 for e in events if e.status == 'cancelled')
    }
    
    total_registered = sum(e.registered_count for e in events)
    total_attended = sum(e.attended_count for e in events)
    total_questions = sum(e.questions_count for e in events)
    
    completed_events = [e for e in events if e.status == 'completed']
    avg_rating = sum(e.avg_rating for e in completed_events) / len(completed_events) if completed_events else 0
    
    return {
        'total_events': total_events,
        'by_status': by_status,
        'total_registered': total_registered,
        'total_attended': total_attended,
        'total_questions': total_questions,
        'average_rating': round(avg_rating, 2),
        'upcoming': LiveEvent.query.filter(
            LiveEvent.candidate_id == candidate_id,
            LiveEvent.status == 'scheduled',
            LiveEvent.starts_at > datetime.utcnow()
        ).count()
    }


# ═══════════════════════════════════════════════════════════════
# توابع کمکی
# ═══════════════════════════════════════════════════════════════

def is_event_full(event_id):
    """
    بررسی پر بودن ظرفیت رویداد
    
    Args:
        event_id: شناسه رویداد
    
    Returns:
        bool
    """
    event = LiveEvent.query.get(event_id)
    if not event or not event.max_participants:
        return False
    
    return event.registered_count >= event.max_participants


def can_citizen_register(event_id, citizen_telegram_id):
    """
    بررسی امکان ثبت‌نام شهروند
    
    Args:
        event_id: شناسه رویداد
        citizen_telegram_id: شناسه تلگرام
    
    Returns:
        tuple (can_register: bool, reason: str)
    """
    event = LiveEvent.query.get(event_id)
    if not event:
        return False, "رویداد یافت نشد"
    
    if event.status == 'cancelled':
        return False, "رویداد لغو شده است"
    
    if event.status == 'completed':
        return False, "رویداد به پایان رسیده است"
    
    # بررسی ثبت‌نام قبلی
    existing = EventRegistration.query.filter_by(
        event_id=event_id,
        citizen_telegram_id=citizen_telegram_id
    ).first()
    
    if existing:
        return False, "قبلاً ثبت‌نام کرده‌اید"
    
    # بررسی ظرفیت
    if event.max_participants and event.registered_count >= event.max_participants:
        return False, "ظرفیت تکمیل است"
    
    return True, "امکان ثبت‌نام وجود دارد"
