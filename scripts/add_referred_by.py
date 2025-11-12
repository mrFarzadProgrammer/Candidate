# -*- coding: utf-8 -*-
"""
Add referred_by column to candidates table
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import db
from candidate_panel.app import app

with app.app_context():
    try:
        # اضافه کردن ستون referred_by
        with db.engine.connect() as conn:
            conn.execute(db.text('ALTER TABLE candidates ADD COLUMN referred_by INTEGER'))
            conn.commit()
        print('✅ ستون referred_by به جدول candidates اضافه شد')
    except Exception as e:
        if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
            print('✅ ستون referred_by از قبل وجود دارد')
        else:
            print(f'❌ خطا: {e}')
