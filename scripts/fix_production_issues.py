# -*- coding: utf-8 -*-
"""
Production-Ready Code Fixer
فیکس خودکار مشکلات بحرانی کد برای Production
"""

import re
import os
from pathlib import Path


def fix_bare_except_blocks(content):
    """
    Replace bare except: with except Exception as e:
    """
    # Pattern: except: followed by pass or code
    pattern = r'(\s+)except:\s*\n'
    replacement = r'\1except Exception as e:\n'
    
    fixed_content = re.sub(pattern, replacement, content)
    
    return fixed_content


def fix_print_statements(content):
    """
    Replace print() with logger.debug()
    """
    # Pattern: print(f"...") or print("...")
    patterns = [
        (r'print\(f"([^"]+)"\)', r'logger.debug(f"\1")'),
        (r"print\(f'([^']+)'\)", r"logger.debug(f'\1')"),
        (r'print\("([^"]+)"\)', r'logger.debug("\1")'),
        (r"print\('([^']+)'\)", r"logger.debug('\1')"),
    ]
    
    fixed_content = content
    for pattern, replacement in patterns:
        fixed_content = re.sub(pattern, replacement, fixed_content)
    
    return fixed_content


def wrap_commits_with_try_except(content):
    """
    Wrap db.session.commit() with try-except blocks
    
    Before:
        db.session.add(obj)
        db.session.commit()
        
    After:
        try:
            db.session.add(obj)
            db.session.commit()
            logger.info("...")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Commit failed: {e}")
            flash("خطا...", "error")
    """
    # This is complex - better to use safe_commit() function
    # Pattern: standalone db.session.commit()
    pattern = r'(\s+)(db\.session\.commit\(\))'
    
    def replace_commit(match):
        indent = match.group(1)
        # Use safe_commit instead
        return f'{indent}if not safe_commit(db):\n{indent}    logger.error("Commit failed")'
    
    # For now, just add comment
    fixed_content = re.sub(
        r'(\s+)(db\.session\.commit\(\))',
        r'\1# TODO: Wrap with try-except\n\1\2',
        content
    )
    
    return fixed_content


def add_logging_import(content):
    """
    Add logging import if not present
    """
    if 'import logging' not in content:
        # Add after other imports
        import_position = content.find('from flask import')
        if import_position != -1:
            # Find end of that line
            end_line = content.find('\n', import_position)
            content = (content[:end_line + 1] + 
                      'import logging\n' + 
                      content[end_line + 1:])
    
    if 'logger = logging.getLogger' not in content:
        # Add after imports
        # Find first function or route
        route_position = content.find('@app.route')
        if route_position != -1:
            content = (content[:route_position] + 
                      '\nlogger = logging.getLogger(__name__)\n\n' + 
                      content[route_position:])
    
    return content


def fix_hardcoded_user_ids(content):
    """
    Replace user_id=1 with session['admin_id']
    """
    # Pattern: user_id=1
    pattern = r'user_id=1(\s*)(#.*)?'
    replacement = r'user_id=session.get("admin_id", 1)\1\2'
    
    fixed_content = re.sub(pattern, replacement, content)
    
    return fixed_content


def process_file(file_path):
    """
    Process a single Python file
    """
    print(f"📝 Processing: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = fix_bare_except_blocks(content)
        content = fix_print_statements(content)
        content = fix_hardcoded_user_ids(content)
        content = add_logging_import(content)
        # Note: wrap_commits is too complex, manual review needed
        
        # Only write if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Fixed!")
            return True
        else:
            print(f"  ⏭️  No changes needed")
            return False
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """
    Main function to fix all Python files
    """
    base_dir = Path(__file__).parent.parent
    
    # Files to process
    files_to_fix = [
        'candidate_panel/app.py',
        'admin_panel/app.py',
        'bot_engine/telegram_bot.py',
        'candidate_panel/party_utils.py',
        'candidate_panel/vip_utils.py',
        'candidate_panel/events_utils.py',
        'candidate_panel/referral_utils.py',
        'candidate_panel/benchmark_utils.py',
        'admin_panel/routes_plan_release.py',
        'admin_panel/routes_data_export.py',
        'security/security_utils.py',
        'data_export/export_system.py',
        'plan_management/gradual_release.py',
    ]
    
    fixed_count = 0
    total_count = len(files_to_fix)
    
    print("="*60)
    print("🔧 Production-Ready Code Fixer")
    print("="*60)
    print(f"\nProcessing {total_count} files...\n")
    
    for file_rel_path in files_to_fix:
        file_path = base_dir / file_rel_path
        if file_path.exists():
            if process_file(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print("\n" + "="*60)
    print(f"✅ Fixed {fixed_count}/{total_count} files")
    print("="*60)
    
    print("\n⚠️  MANUAL REVIEW NEEDED:")
    print("1. db.session.commit() - Replace with safe_commit(db)")
    print("2. Complex exception handling - Add specific except blocks")
    print("3. Input validation - Add validate_form_data() where needed")
    print("\n💡 Run tests after applying fixes!")


if __name__ == '__main__':
    main()
