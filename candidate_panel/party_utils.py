"""
توابع کمکی برای مدیریت احزاب سیاسی و ائتلاف‌های انتخاباتی
"""

from database.models import (
    db, PoliticalParty, PartyMembership, 
    ElectoralCoalition, CoalitionMembership,
    Candidate
)
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_


# ================== احزاب سیاسی ==================

def create_party(name, leader_candidate_id, description='', ideology='', **kwargs):
    """
    ایجاد حزب جدید
    
    Args:
        name: نام حزب
        leader_candidate_id: ID رهبر حزب
        description: توضیحات
        ideology: ایدئولوژی (اصلاح‌طلب، اصولگرا، میانه‌رو، مستقل)
        **kwargs: فیلدهای اختیاری (logo, color_primary, manifesto, ...)
    
    Returns:
        PoliticalParty: حزب ایجاد شده
    """
    party = PoliticalParty(
        name=name,
        leader_candidate_id=leader_candidate_id,
        description=description,
        ideology=ideology,
        **kwargs
    )
    
    db.session.add(party)
    db.session.flush()  # برای گرفتن party.id
    
    # رهبر به صورت خودکار عضو می‌شود با دسترسی کامل
    add_member_to_party(
        party_id=party.id,
        candidate_id=leader_candidate_id,
        role='leader',
        can_manage_party=True,
        can_manage_members=True,
        can_send_broadcast=True,
        can_view_analytics=True,
        can_create_events=True,
        is_approved=True
    )
    
    db.session.commit()
    return party


def get_party_by_id(party_id):
    """دریافت اطلاعات حزب"""
    return PoliticalParty.query.get(party_id)


def get_candidate_parties(candidate_id):
    """
    دریافت لیست احزابی که نامزد عضو آن‌هاست
    
    Returns:
        List[Tuple]: (PoliticalParty, PartyMembership)
    """
    return db.session.query(PoliticalParty, PartyMembership).join(
        PartyMembership, PoliticalParty.id == PartyMembership.party_id
    ).filter(
        PartyMembership.candidate_id == candidate_id,
        PartyMembership.is_active == True
    ).all()


def update_party(party_id, **kwargs):
    """
    آپدیت اطلاعات حزب
    
    Args:
        party_id: ID حزب
        **kwargs: فیلدهای قابل آپدیت
    """
    party = PoliticalParty.query.get(party_id)
    if not party:
        return None
    
    for key, value in kwargs.items():
        if hasattr(party, key):
            setattr(party, key, value)
    
    party.updated_at = datetime.utcnow()
    db.session.commit()
    return party


def delete_party(party_id):
    """حذف حزب (غیرفعال کردن)"""
    party = PoliticalParty.query.get(party_id)
    if party:
        party.is_active = False
        db.session.commit()
        return True
    return False


# ================== عضویت در حزب ==================

def add_member_to_party(party_id, candidate_id, role='member', position='', 
                        can_manage_party=False, can_manage_members=False,
                        can_send_broadcast=False, can_view_analytics=True,
                        can_create_events=False, is_approved=False):
    """
    افزودن عضو به حزب
    
    Args:
        party_id: ID حزب
        candidate_id: ID نامزد
        role: نقش (leader, deputy, secretary, member, supporter)
        position: موقعیت (دبیر استان، ...)
        can_*: دسترسی‌ها
        is_approved: تایید شده یا نیاز به تایید
    
    Returns:
        PartyMembership یا None
    """
    # چک کردن عضویت قبلی
    existing = PartyMembership.query.filter_by(
        party_id=party_id,
        candidate_id=candidate_id
    ).first()
    
    if existing:
        if existing.is_active:
            return None  # قبلاً عضو است
        else:
            # فعال‌سازی مجدد
            existing.is_active = True
            existing.joined_at = datetime.utcnow()
            existing.role = role
            existing.is_approved = is_approved
            db.session.commit()
            return existing
    
    # ایجاد عضویت جدید
    membership = PartyMembership(
        party_id=party_id,
        candidate_id=candidate_id,
        role=role,
        position=position,
        can_manage_party=can_manage_party,
        can_manage_members=can_manage_members,
        can_send_broadcast=can_send_broadcast,
        can_view_analytics=can_view_analytics,
        can_create_events=can_create_events,
        is_approved=is_approved
    )
    
    db.session.add(membership)
    
    # آپدیت تعداد اعضا
    party = PoliticalParty.query.get(party_id)
    if party:
        party.total_members = PartyMembership.query.filter_by(
            party_id=party_id,
            is_active=True,
            is_approved=True
        ).count()
        party.total_candidates = party.total_members
    
    db.session.commit()
    return membership


def remove_member_from_party(party_id, candidate_id):
    """حذف عضو از حزب"""
    membership = PartyMembership.query.filter_by(
        party_id=party_id,
        candidate_id=candidate_id
    ).first()
    
    if membership:
        membership.is_active = False
        membership.left_at = datetime.utcnow()
        
        # آپدیت تعداد اعضا
        party = PoliticalParty.query.get(party_id)
        if party:
            party.total_members = PartyMembership.query.filter_by(
                party_id=party_id,
                is_active=True,
                is_approved=True
            ).count()
            party.total_candidates = party.total_members
        
        db.session.commit()
        return True
    return False


def update_member_role(party_id, candidate_id, role, position='', **permissions):
    """
    تغییر نقش و دسترسی‌های عضو
    
    Args:
        party_id: ID حزب
        candidate_id: ID نامزد
        role: نقش جدید
        position: موقعیت جدید
        **permissions: دسترسی‌ها (can_manage_party, can_manage_members, ...)
    """
    membership = PartyMembership.query.filter_by(
        party_id=party_id,
        candidate_id=candidate_id
    ).first()
    
    if membership:
        membership.role = role
        if position:
            membership.position = position
        
        for key, value in permissions.items():
            if hasattr(membership, key):
                setattr(membership, key, value)
        
        db.session.commit()
        return membership
    return None


def approve_member(party_id, candidate_id):
    """تایید عضویت"""
    membership = PartyMembership.query.filter_by(
        party_id=party_id,
        candidate_id=candidate_id
    ).first()
    
    if membership:
        membership.is_approved = True
        membership.approved_at = datetime.utcnow()
        
        # آپدیت تعداد اعضا
        party = PoliticalParty.query.get(party_id)
        if party:
            party.total_members = PartyMembership.query.filter_by(
                party_id=party_id,
                is_active=True,
                is_approved=True
            ).count()
            party.total_candidates = party.total_members
        
        db.session.commit()
        return True
    return False


def get_party_members(party_id, include_pending=False):
    """
    دریافت لیست اعضای حزب
    
    Args:
        party_id: ID حزب
        include_pending: شامل اعضای تایید نشده
    
    Returns:
        List[Tuple]: (Candidate, PartyMembership)
    """
    query = db.session.query(Candidate, PartyMembership).join(
        PartyMembership, Candidate.id == PartyMembership.candidate_id
    ).filter(
        PartyMembership.party_id == party_id,
        PartyMembership.is_active == True
    )
    
    if not include_pending:
        query = query.filter(PartyMembership.is_approved == True)
    
    return query.all()


def get_pending_members(party_id):
    """دریافت اعضای منتظر تایید"""
    return db.session.query(Candidate, PartyMembership).join(
        PartyMembership, Candidate.id == PartyMembership.candidate_id
    ).filter(
        PartyMembership.party_id == party_id,
        PartyMembership.is_active == True,
        PartyMembership.is_approved == False
    ).all()


def check_member_permission(party_id, candidate_id, permission):
    """
    چک کردن دسترسی عضو
    
    Args:
        party_id: ID حزب
        candidate_id: ID نامزد
        permission: نام دسترسی (can_manage_party, can_send_broadcast, ...)
    
    Returns:
        bool
    """
    membership = PartyMembership.query.filter_by(
        party_id=party_id,
        candidate_id=candidate_id,
        is_active=True,
        is_approved=True
    ).first()
    
    if not membership:
        return False
    
    return getattr(membership, permission, False)


# ================== ائتلاف‌های انتخاباتی ==================

def create_coalition(name, coordinator_candidate_id, election_type, election_year, **kwargs):
    """
    ایجاد ائتلاف انتخاباتی
    
    Args:
        name: نام ائتلاف
        coordinator_candidate_id: ID هماهنگ‌کننده
        election_type: نوع انتخابات (مجلس، شورا، ریاست‌جمهوری)
        election_year: سال انتخابات
        **kwargs: فیلدهای اختیاری
    
    Returns:
        ElectoralCoalition
    """
    coalition = ElectoralCoalition(
        name=name,
        coordinator_candidate_id=coordinator_candidate_id,
        election_type=election_type,
        election_year=election_year,
        formed_at=datetime.utcnow(),
        **kwargs
    )
    
    db.session.add(coalition)
    db.session.commit()
    return coalition


def add_party_to_coalition(coalition_id, party_id=None, candidate_id=None, **kwargs):
    """
    افزودن حزب یا نامزد مستقل به ائتلاف
    
    Args:
        coalition_id: ID ائتلاف
        party_id: ID حزب (اختیاری)
        candidate_id: ID نامزد مستقل (اختیاری)
        **kwargs: فیلدهای اختیاری (vote_share_percentage, agreement_text, ...)
    
    Returns:
        CoalitionMembership یا None
    """
    if not party_id and not candidate_id:
        return None
    
    # چک کردن عضویت قبلی
    existing = CoalitionMembership.query.filter_by(
        coalition_id=coalition_id,
        party_id=party_id,
        candidate_id=candidate_id
    ).first()
    
    if existing and existing.is_active:
        return None  # قبلاً عضو است
    
    membership = CoalitionMembership(
        coalition_id=coalition_id,
        party_id=party_id,
        candidate_id=candidate_id,
        **kwargs
    )
    
    db.session.add(membership)
    
    # آپدیت آمار
    coalition = ElectoralCoalition.query.get(coalition_id)
    if coalition:
        coalition.total_parties = CoalitionMembership.query.filter_by(
            coalition_id=coalition_id,
            is_active=True
        ).filter(CoalitionMembership.party_id != None).count()
        
        coalition.total_candidates = CoalitionMembership.query.filter_by(
            coalition_id=coalition_id,
            is_active=True
        ).filter(CoalitionMembership.candidate_id != None).count()
    
    db.session.commit()
    return membership


def remove_from_coalition(coalition_id, party_id=None, candidate_id=None):
    """حذف از ائتلاف"""
    query = CoalitionMembership.query.filter_by(coalition_id=coalition_id)
    
    if party_id:
        query = query.filter_by(party_id=party_id)
    if candidate_id:
        query = query.filter_by(candidate_id=candidate_id)
    
    membership = query.first()
    
    if membership:
        membership.is_active = False
        membership.left_at = datetime.utcnow()
        
        # آپدیت آمار
        coalition = ElectoralCoalition.query.get(coalition_id)
        if coalition:
            coalition.total_parties = CoalitionMembership.query.filter_by(
                coalition_id=coalition_id,
                is_active=True
            ).filter(CoalitionMembership.party_id != None).count()
            
            coalition.total_candidates = CoalitionMembership.query.filter_by(
                coalition_id=coalition_id,
                is_active=True
            ).filter(CoalitionMembership.candidate_id != None).count()
        
        db.session.commit()
        return True
    return False


def get_coalition_members(coalition_id):
    """
    دریافت اعضای ائتلاف (احزاب + نامزدهای مستقل)
    
    Returns:
        dict: {
            'parties': [(PoliticalParty, CoalitionMembership)],
            'candidates': [(Candidate, CoalitionMembership)]
        }
    """
    # احزاب عضو
    parties = db.session.query(PoliticalParty, CoalitionMembership).join(
        CoalitionMembership, PoliticalParty.id == CoalitionMembership.party_id
    ).filter(
        CoalitionMembership.coalition_id == coalition_id,
        CoalitionMembership.is_active == True
    ).all()
    
    # نامزدهای مستقل عضو
    candidates = db.session.query(Candidate, CoalitionMembership).join(
        CoalitionMembership, Candidate.id == CoalitionMembership.candidate_id
    ).filter(
        CoalitionMembership.coalition_id == coalition_id,
        CoalitionMembership.is_active == True,
        CoalitionMembership.party_id == None  # فقط مستقل‌ها
    ).all()
    
    return {
        'parties': parties,
        'candidates': candidates
    }


def get_candidate_coalitions(candidate_id):
    """دریافت ائتلاف‌های یک نامزد"""
    return db.session.query(ElectoralCoalition, CoalitionMembership).join(
        CoalitionMembership, ElectoralCoalition.id == CoalitionMembership.coalition_id
    ).filter(
        CoalitionMembership.candidate_id == candidate_id,
        CoalitionMembership.is_active == True
    ).all()


def update_coalition(coalition_id, **kwargs):
    """آپدیت اطلاعات ائتلاف"""
    coalition = ElectoralCoalition.query.get(coalition_id)
    if not coalition:
        return None
    
    for key, value in kwargs.items():
        if hasattr(coalition, key):
            setattr(coalition, key, value)
    
    db.session.commit()
    return coalition


def dissolve_coalition(coalition_id):
    """انحلال ائتلاف"""
    coalition = ElectoralCoalition.query.get(coalition_id)
    if coalition:
        coalition.status = 'dissolved'
        coalition.dissolved_at = datetime.utcnow()
        coalition.is_active = False
        db.session.commit()
        return True
    return False


# ================== آمار و گزارش ==================

def get_party_statistics(party_id):
    """
    آمار کامل حزب
    
    Returns:
        dict
    """
    party = PoliticalParty.query.get(party_id)
    if not party:
        return None
    
    # تعداد اعضا بر اساس نقش
    members_by_role = db.session.query(
        PartyMembership.role,
        func.count(PartyMembership.id)
    ).filter_by(
        party_id=party_id,
        is_active=True,
        is_approved=True
    ).group_by(PartyMembership.role).all()
    
    # اعضای منتظر تایید
    pending_count = PartyMembership.query.filter_by(
        party_id=party_id,
        is_active=True,
        is_approved=False
    ).count()
    
    # ائتلاف‌های فعال
    active_coalitions = db.session.query(ElectoralCoalition).join(
        CoalitionMembership, ElectoralCoalition.id == CoalitionMembership.coalition_id
    ).filter(
        CoalitionMembership.party_id == party_id,
        CoalitionMembership.is_active == True,
        ElectoralCoalition.is_active == True
    ).count()
    
    return {
        'total_members': party.total_members,
        'members_by_role': dict(members_by_role),
        'pending_approvals': pending_count,
        'active_coalitions': active_coalitions,
        'subscription_active': party.subscription_is_active,
        'is_verified': party.is_verified
    }


def get_coalition_statistics(coalition_id):
    """آمار کامل ائتلاف"""
    coalition = ElectoralCoalition.query.get(coalition_id)
    if not coalition:
        return None
    
    members = get_coalition_members(coalition_id)
    
    # جمع آمار
    total_estimated_votes = db.session.query(
        func.coalesce(func.sum(PoliticalParty.total_votes_estimate), 0)
    ).join(
        CoalitionMembership, PoliticalParty.id == CoalitionMembership.party_id
    ).filter(
        CoalitionMembership.coalition_id == coalition_id,
        CoalitionMembership.is_active == True
    ).scalar() or 0
    
    return {
        'total_parties': len(members['parties']),
        'total_independent_candidates': len(members['candidates']),
        'total_members': len(members['parties']) + len(members['candidates']),
        'estimated_votes': int(total_estimated_votes),
        'status': coalition.status,
        'days_to_election': (coalition.election_date - datetime.utcnow().date()).days if coalition.election_date else None
    }


def search_parties(query='', ideology=None, is_verified=None, limit=20):
    """جستجوی احزاب"""
    filters = [PoliticalParty.is_active == True]
    
    if query:
        filters.append(
            or_(
                PoliticalParty.name.ilike(f'%{query}%'),
                PoliticalParty.description.ilike(f'%{query}%')
            )
        )
    
    if ideology:
        filters.append(PoliticalParty.ideology == ideology)
    
    if is_verified is not None:
        filters.append(PoliticalParty.is_verified == is_verified)
    
    return PoliticalParty.query.filter(and_(*filters)).limit(limit).all()
