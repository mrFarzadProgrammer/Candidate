#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bulk Security Decorator Application
====================================
جایگزینی @login_required با @secure_route() در POST routes
"""

import re

def apply_bulk_security(file_path):
    """اعمال دسته‌جمعی security به POST routes"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern: @app.route با POST + @login_required در خط بعد
    # Replace @login_required با @secure_route()
    
    pattern = r'(@app\.route\([^)]*methods=[^)]*POST[^)]*\)[^\n]*\n)@login_required(\s*\ndef)'
    
    def replace_decorator(match):
        route_line = match.group(1)
        def_line = match.group(2)
        return f'{route_line}@secure_route(){def_line}'
    
    content = re.sub(pattern, replace_decorator, content)
    
    # شمارش تغییرات
    changes = content.count('@secure_route()') - original_content.count('@secure_route()')
    
    if changes > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {changes} route امن شد")
        return changes
    else:
        print("ℹ️ همه routes قبلاً امن شده‌اند")
        return 0

# اعمال به candidate_panel
changes = apply_bulk_security('candidate_panel/app.py')
print(f"\n📊 خلاصه: {changes} POST route با @secure_route() امن شد")
