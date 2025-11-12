# -*- coding: utf-8 -*-
"""
تست‌های سیستم حزبی و ائتلاف
Political Party and Coalition System Tests
"""

import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from candidate_panel.app import app, db
from database.models import (
    Candidate, PoliticalParty, PartyMember, PartyRole,
    Coalition, CoalitionMember
)
from candidate_panel.party_utils import PartyManager
from security.security_utils import hash_password


@pytest.fixture
def client():
    """فیکسچر test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def test_candidates():
    """فیکسچر کاندیدهای تست"""
    with app.app_context():
        candidates = []
        for i in range(10):
            candidate = Candidate(
                name=f'کاندید {i}',
                username=f'candidate_{i}',
                password=hash_password('Pass123'),
                telegram_token=f'123{i}:ABC',
                bot_username=f'bot_{i}'
            )
            db.session.add(candidate)
            candidates.append(candidate)
        
        db.session.commit()
        return candidates


class TestPartyCreation:
    """تست‌های ایجاد حزب"""
    
    def test_create_party_with_founder(self, client, test_candidates):
        """تست ایجاد حزب با بنیان‌گذار"""
        manager = PartyManager()
        founder = test_candidates[0]
        
        party = manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder.id,
            description='حزب آزادی و دموکراسی',
            ideology='لیبرال'
        )
        
        assert party is not None
        assert party.name == 'حزب آزادی'
        assert party.founder_id == founder.id
    
    def test_founder_becomes_party_leader(self, client, test_candidates):
        """تست تبدیل بنیان‌گذار به رهبر حزب"""
        manager = PartyManager()
        founder = test_candidates[0]
        
        party = manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder.id
        )
        
        # بررسی عضویت بنیان‌گذار
        membership = PartyMember.query.filter_by(
            party_id=party.id,
            candidate_id=founder.id
        ).first()
        
        assert membership is not None
        assert membership.role == 'leader'
        assert membership.is_approved is True
    
    def test_cannot_create_party_with_same_name(self, client, test_candidates):
        """تست عدم امکان ایجاد حزب با نام تکراری"""
        manager = PartyManager()
        founder1 = test_candidates[0]
        founder2 = test_candidates[1]
        
        # ایجاد حزب اول
        manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder1.id
        )
        
        # تلاش برای ایجاد حزب دوم با همین نام
        with pytest.raises(ValueError):
            manager.create_party(
                name='حزب آزادی',
                name_en='Freedom Party',
                founder_id=founder2.id
            )


class TestPartyMembership:
    """تست‌های عضویت در حزب"""
    
    def test_add_member_to_party(self, client, test_candidates):
        """تست اضافه کردن عضو به حزب"""
        manager = PartyManager()
        founder = test_candidates[0]
        new_member = test_candidates[1]
        
        # ایجاد حزب
        party = manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder.id
        )
        
        # درخواست عضویت
        success = manager.request_membership(
            party_id=party.id,
            candidate_id=new_member.id
        )
        
        assert success is True
        
        # بررسی عضویت (منتظر تایید)
        membership = PartyMember.query.filter_by(
            party_id=party.id,
            candidate_id=new_member.id
        ).first()
        
        assert membership is not None
        assert membership.is_approved is False
    
    def test_add_member_requires_approval(self, client, test_candidates):
        """تست نیاز به تایید برای عضویت"""
        manager = PartyManager()
        founder = test_candidates[0]
        new_member = test_candidates[1]
        
        party = manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder.id
        )
        
        # درخواست عضویت
        manager.request_membership(party.id, new_member.id)
        
        # عضو نباید بتونه قبل از تایید کار کنه
        can_act = manager.can_member_act(party.id, new_member.id)
        assert can_act is False
        
        # رهبر تایید می‌کنه
        manager.approve_membership(party.id, new_member.id, founder.id)
        
        # حالا می‌تونه کار کنه
        can_act = manager.can_member_act(party.id, new_member.id)
        assert can_act is True
    
    def test_remove_member_from_party(self, client, test_candidates):
        """تست حذف عضو از حزب"""
        manager = PartyManager()
        founder = test_candidates[0]
        member = test_candidates[1]
        
        party = manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder.id
        )
        
        # اضافه و تایید عضو
        manager.request_membership(party.id, member.id)
        manager.approve_membership(party.id, member.id, founder.id)
        
        # حذف عضو
        success = manager.remove_member(party.id, member.id, founder.id)
        
        assert success is True
        
        # بررسی حذف
        membership = PartyMember.query.filter_by(
            party_id=party.id,
            candidate_id=member.id
        ).first()
        
        assert membership is None or membership.status == 'removed'
    
    def test_member_can_leave_party(self, client, test_candidates):
        """تست خروج داوطلبانه از حزب"""
        manager = PartyManager()
        founder = test_candidates[0]
        member = test_candidates[1]
        
        party = manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder.id
        )
        
        manager.request_membership(party.id, member.id)
        manager.approve_membership(party.id, member.id, founder.id)
        
        # خروج از حزب
        success = manager.leave_party(party.id, member.id)
        
        assert success is True


class TestPartyRoles:
    """تست‌های نقش‌های حزبی"""
    
    def test_assign_role_to_member(self, client, test_candidates):
        """تست تخصیص نقش به عضو"""
        manager = PartyManager()
        founder = test_candidates[0]
        member = test_candidates[1]
        
        party = manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder.id
        )
        
        manager.request_membership(party.id, member.id)
        manager.approve_membership(party.id, member.id, founder.id)
        
        # تخصیص نقش نائب رئیس
        success = manager.assign_role(
            party_id=party.id,
            candidate_id=member.id,
            role='deputy_leader',
            assigned_by=founder.id
        )
        
        assert success is True
        
        # بررسی نقش
        membership = PartyMember.query.filter_by(
            party_id=party.id,
            candidate_id=member.id
        ).first()
        
        assert membership.role == 'deputy_leader'
    
    def test_role_permissions(self, client, test_candidates):
        """تست مجوزهای نقش‌ها"""
        manager = PartyManager()
        founder = test_candidates[0]
        member = test_candidates[1]
        
        party = manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder.id
        )
        
        manager.request_membership(party.id, member.id)
        manager.approve_membership(party.id, member.id, founder.id)
        
        # عضو عادی نمی‌تونه عضو جدید تایید کنه
        can_approve = manager.has_permission(
            party.id,
            member.id,
            'approve_members'
        )
        assert can_approve is False
        
        # تخصیص نقش moderator
        manager.assign_role(party.id, member.id, 'moderator', founder.id)
        
        # حالا می‌تونه تایید کنه
        can_approve = manager.has_permission(
            party.id,
            member.id,
            'approve_members'
        )
        assert can_approve is True
    
    def test_only_leader_can_change_roles(self, client, test_candidates):
        """تست فقط رهبر می‌تونه نقش‌ها رو تغییر بده"""
        manager = PartyManager()
        founder = test_candidates[0]
        member1 = test_candidates[1]
        member2 = test_candidates[2]
        
        party = manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder.id
        )
        
        # اضافه کردن دو عضو
        manager.request_membership(party.id, member1.id)
        manager.approve_membership(party.id, member1.id, founder.id)
        
        manager.request_membership(party.id, member2.id)
        manager.approve_membership(party.id, member2.id, founder.id)
        
        # member1 نمی‌تونه نقش member2 رو تغییر بده
        with pytest.raises(PermissionError):
            manager.assign_role(
                party.id,
                member2.id,
                'moderator',
                assigned_by=member1.id
            )


class TestCoalitions:
    """تست‌های ائتلاف"""
    
    def test_create_coalition(self, client, test_candidates):
        """تست ایجاد ائتلاف"""
        manager = PartyManager()
        founder1 = test_candidates[0]
        founder2 = test_candidates[1]
        
        # ایجاد دو حزب
        party1 = manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder1.id
        )
        
        party2 = manager.create_party(
            name='حزب رفاه',
            name_en='Welfare Party',
            founder_id=founder2.id
        )
        
        # ایجاد ائتلاف
        coalition = manager.create_coalition(
            name='ائتلاف اصلاح‌طلبان',
            name_en='Reform Coalition',
            description='ائتلاف احزاب اصلاح‌طلب',
            created_by=founder1.id
        )
        
        assert coalition is not None
        assert coalition.name == 'ائتلاف اصلاح‌طلبان'
    
    def test_add_party_to_coalition(self, client, test_candidates):
        """تست اضافه کردن حزب به ائتلاف"""
        manager = PartyManager()
        founder1 = test_candidates[0]
        founder2 = test_candidates[1]
        
        party1 = manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder1.id
        )
        
        party2 = manager.create_party(
            name='حزب رفاه',
            name_en='Welfare Party',
            founder_id=founder2.id
        )
        
        coalition = manager.create_coalition(
            name='ائتلاف اصلاح‌طلبان',
            name_en='Reform Coalition',
            created_by=founder1.id
        )
        
        # اضافه کردن احزاب به ائتلاف
        success1 = manager.add_party_to_coalition(
            coalition.id,
            party1.id,
            added_by=founder1.id
        )
        
        success2 = manager.add_party_to_coalition(
            coalition.id,
            party2.id,
            added_by=founder1.id
        )
        
        assert success1 is True
        assert success2 is True
        
        # بررسی عضویت
        members = CoalitionMember.query.filter_by(
            coalition_id=coalition.id
        ).all()
        
        assert len(members) == 2
    
    def test_remove_party_from_coalition(self, client, test_candidates):
        """تست حذف حزب از ائتلاف"""
        manager = PartyManager()
        founder1 = test_candidates[0]
        founder2 = test_candidates[1]
        
        party1 = manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder1.id
        )
        
        party2 = manager.create_party(
            name='حزب رفاه',
            name_en='Welfare Party',
            founder_id=founder2.id
        )
        
        coalition = manager.create_coalition(
            name='ائتلاف اصلاح‌طلبان',
            name_en='Reform Coalition',
            created_by=founder1.id
        )
        
        manager.add_party_to_coalition(coalition.id, party1.id, founder1.id)
        manager.add_party_to_coalition(coalition.id, party2.id, founder1.id)
        
        # حذف یک حزب
        success = manager.remove_party_from_coalition(
            coalition.id,
            party2.id,
            removed_by=founder1.id
        )
        
        assert success is True
        
        # بررسی
        members = CoalitionMember.query.filter_by(
            coalition_id=coalition.id
        ).all()
        
        assert len(members) == 1
        assert members[0].party_id == party1.id


class TestPartyStatistics:
    """تست‌های آمار حزبی"""
    
    def test_get_party_member_count(self, client, test_candidates):
        """تست شمارش اعضای حزب"""
        manager = PartyManager()
        founder = test_candidates[0]
        
        party = manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder.id
        )
        
        # اضافه کردن 5 عضو
        for i in range(1, 6):
            manager.request_membership(party.id, test_candidates[i].id)
            manager.approve_membership(
                party.id,
                test_candidates[i].id,
                founder.id
            )
        
        # شمارش (5 عضو + 1 بنیان‌گذار)
        count = manager.get_member_count(party.id)
        assert count == 6
    
    def test_get_party_activity_score(self, client, test_candidates):
        """تست محاسبه امتیاز فعالیت حزب"""
        manager = PartyManager()
        founder = test_candidates[0]
        
        party = manager.create_party(
            name='حزب آزادی',
            name_en='Freedom Party',
            founder_id=founder.id
        )
        
        # امتیاز فعالیت (بر اساس تعداد اعضا، فعالیت‌ها، و...)
        score = manager.get_activity_score(party.id)
        
        assert score >= 0
        assert isinstance(score, (int, float))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
