# -*- coding: utf-8 -*-
"""
Recreate referral tables with new structure
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import db, ReferralProgram, ReferralReward
from candidate_panel.app import app

with app.app_context():
    try:
        # حذف جداول قدیمی
        with db.engine.connect() as conn:
            conn.execute(db.text('DROP TABLE IF EXISTS referral_rewards'))
            conn.execute(db.text('DROP TABLE IF EXISTS referral_programs'))
            conn.commit()
        print('✅ جداول قدیمی حذف شدند')
        
        # ساخت جداول جدید
        ReferralProgram.__table__.create(db.engine)
        ReferralReward.__table__.create(db.engine)
        print('✅ جداول جدید ساخته شدند')
        
    except Exception as e:
        print(f'❌ خطا: {e}')
