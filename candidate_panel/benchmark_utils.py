"""
محاسبات Benchmark و Ranking
این فایل شامل توابع کمکی برای محاسبه آمار بازار و رتبه‌بندی نامزدها است
"""

from database.models import (db, Candidate, Analytics, Plan, PlanPurchase,
                            MarketplaceBenchmark, CandidateRanking, BotUser,
                            Message, CitizenContribution)
from datetime import datetime, timedelta
from sqlalchemy import func
import statistics


def calculate_marketplace_benchmarks():
    """
    محاسبه آمار بازار برای تمام پلن‌ها
    این تابع روزانه اجرا می‌شود
    """
    today = datetime.utcnow().date()
    
    # لیست تمام پلن‌ها
    plans = Plan.query.filter_by(is_active=True).all()
    
    for plan in plans:
        # پیدا کردن نامزدهایی که این پلن رو دارن
        candidates_with_plan = db.session.query(Candidate).join(
            PlanPurchase
        ).filter(
            PlanPurchase.plan_id == plan.id,
            PlanPurchase.is_active == True
        ).all()
        
        if not candidates_with_plan:
            continue
        
        # جمع‌آوری آمار
        messages_list = []
        users_list = []
        contributions_list = []
        
        for candidate in candidates_with_plan:
            analytics = Analytics.query.filter_by(candidate_id=candidate.id).first()
            if analytics:
                messages_list.append(analytics.total_messages or 0)
                users_list.append(analytics.total_users or 0)
            
            contributions = CitizenContribution.query.filter_by(
                candidate_id=candidate.id
            ).count()
            contributions_list.append(contributions)
        
        # محاسبه میانگین و صدک‌ها
        if messages_list:
            avg_messages = statistics.mean(messages_list)
            median_messages = statistics.median(messages_list)
            min_messages = min(messages_list)
            max_messages = max(messages_list)
            
            # صدک‌ها
            sorted_messages = sorted(messages_list)
            n = len(sorted_messages)
            top_10_idx = int(n * 0.9)
            top_25_idx = int(n * 0.75)
            bottom_25_idx = int(n * 0.25)
            
            top_10_percent = sorted_messages[top_10_idx] if top_10_idx < n else max_messages
            top_25_percent = sorted_messages[top_25_idx] if top_25_idx < n else max_messages
            bottom_25_percent = sorted_messages[bottom_25_idx] if bottom_25_idx < n else min_messages
        else:
            avg_messages = median_messages = min_messages = max_messages = 0
            top_10_percent = top_25_percent = bottom_25_percent = 0
        
        avg_users = statistics.mean(users_list) if users_list else 0
        avg_contributions = statistics.mean(contributions_list) if contributions_list else 0
        
        # ذخیره در دیتابیس
        benchmark = MarketplaceBenchmark.query.filter_by(
            date=today,
            plan_code=plan.code
        ).first()
        
        if not benchmark:
            benchmark = MarketplaceBenchmark(
                date=today,
                plan_code=plan.code
            )
        
        benchmark.avg_daily_messages = round(avg_messages, 2)
        benchmark.avg_bot_users = round(avg_users, 2)
        benchmark.avg_citizen_contributions = round(avg_contributions, 2)
        benchmark.min_messages = min_messages
        benchmark.max_messages = max_messages
        benchmark.median_messages = int(median_messages)
        benchmark.top_10_percent_messages = top_10_percent
        benchmark.top_25_percent_messages = top_25_percent
        benchmark.bottom_25_percent_messages = bottom_25_percent
        benchmark.sample_size = len(candidates_with_plan)
        
        db.session.add(benchmark)
    
    safe_commit(db, "Database commit failed")
    logger.debug(f"✅ Benchmark برای {len(plans)} پلن محاسبه شد")


def calculate_candidate_ranking(candidate_id):
    """
    محاسبه رتبه یک نامزد خاص
    """
    today = datetime.utcnow().date()
    
    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        return None
    
    # پلن فعلی
    active_purchase = PlanPurchase.query.filter_by(
        candidate_id=candidate_id,
        is_active=True
    ).first()
    
    plan_code = active_purchase.plan.code if active_purchase else 'trial'
    
    # آمار خود نامزد
    analytics = Analytics.query.filter_by(candidate_id=candidate_id).first()
    my_messages = analytics.total_messages if analytics else 0
    my_users = analytics.total_users if analytics else 0
    
    # آمار همه نامزدها
    all_analytics = db.session.query(Analytics).join(Candidate).filter(
        Candidate.is_active == True
    ).all()
    
    all_messages = [a.total_messages or 0 for a in all_analytics]
    all_messages_sorted = sorted(all_messages, reverse=True)
    
    # محاسبه رتبه
    try:
        overall_rank = all_messages_sorted.index(my_messages) + 1
    except ValueError:
        overall_rank = len(all_messages_sorted)
    
    # محاسبه صدک (بهتر از چند درصد)
    better_than_count = sum(1 for m in all_messages if my_messages > m)
    percentile = (better_than_count / len(all_messages) * 100) if all_messages else 0
    
    # مقایسه با میانگین
    avg_messages = statistics.mean(all_messages) if all_messages else 0
    messages_vs_avg = ((my_messages - avg_messages) / avg_messages * 100) if avg_messages > 0 else 0
    
    # امتیاز کلی (weighted score)
    messages_score = (my_messages / max(all_messages)) * 40 if all_messages else 0
    users_score = (my_users / max([a.total_users or 0 for a in all_analytics])) * 30 if all_analytics else 0
    engagement_score = 20  # placeholder
    growth_score = 10  # placeholder
    
    total_score = messages_score + users_score + engagement_score + growth_score
    
    # ذخیره
    ranking = CandidateRanking.query.filter_by(
        candidate_id=candidate_id,
        date=today
    ).first()
    
    if not ranking:
        ranking = CandidateRanking(
            candidate_id=candidate_id,
            date=today
        )
    
    ranking.overall_rank = overall_rank
    ranking.percentile = round(percentile, 1)
    ranking.total_score = round(total_score, 2)
    ranking.messages_score = round(messages_score, 2)
    ranking.users_score = round(users_score, 2)
    ranking.engagement_score = engagement_score
    ranking.growth_score = growth_score
    ranking.total_messages = my_messages
    ranking.total_bot_users = my_users
    ranking.messages_vs_avg = round(messages_vs_avg, 1)
    
    db.session.add(ranking)
    safe_commit(db, "Database commit failed")
    
    return ranking


def get_candidate_benchmark_comparison(candidate_id):
    """
    دریافت مقایسه نامزد با benchmark بازار
    """
    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        return None
    
    # پلن فعلی
    active_purchase = PlanPurchase.query.filter_by(
        candidate_id=candidate_id,
        is_active=True
    ).first()
    
    plan_code = active_purchase.plan.code if active_purchase else 'trial'
    
    # آخرین benchmark
    benchmark = MarketplaceBenchmark.query.filter_by(
        plan_code=plan_code
    ).order_by(MarketplaceBenchmark.date.desc()).first()
    
    # آمار خود نامزد
    analytics = Analytics.query.filter_by(candidate_id=candidate_id).first()
    my_messages = analytics.total_messages if analytics else 0
    my_users = analytics.total_users if analytics else 0
    
    # آخرین رتبه
    ranking = CandidateRanking.query.filter_by(
        candidate_id=candidate_id
    ).order_by(CandidateRanking.date.desc()).first()
    
    return {
        'my_stats': {
            'messages': my_messages,
            'users': my_users,
            'rank': ranking.overall_rank if ranking else None,
            'percentile': ranking.percentile if ranking else None
        },
        'benchmark': {
            'avg_messages': benchmark.avg_daily_messages if benchmark else 0,
            'median_messages': benchmark.median_messages if benchmark else 0,
            'top_10_messages': benchmark.top_10_percent_messages if benchmark else 0,
            'sample_size': benchmark.sample_size if benchmark else 0
        },
        'comparison': {
            'vs_average': ranking.messages_vs_avg if ranking else 0,
            'better_than_percent': ranking.percentile if ranking else 0
        },
        'plan_code': plan_code
    }


def calculate_all_rankings():
    """
    محاسبه رتبه برای تمام نامزدهای فعال
    این تابع روزانه اجرا می‌شود
    """
    candidates = Candidate.query.filter_by(is_active=True).all()
    
    for candidate in candidates:
        try:
            calculate_candidate_ranking(candidate.id)
        except Exception as e:
            logger.debug(f"خطا در محاسبه رتبه {candidate.id}: {e}")
    
    logger.debug(f"✅ رتبه‌بندی {len(candidates)} نامزد انجام شد")
