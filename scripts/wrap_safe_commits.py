# -*- coding: utf-8 -*-
"""
Safe Commit Wrapper
جایگزینی db.session.commit() با safe_commit(db)
"""

import re
from pathlib import Path


def wrap_commits_intelligently(content):
    """
    Replace db.session.commit() with safe_commit(db)
    """
    # Add import if needed
    if 'from utils.db_utils import safe_commit' not in content:
        # Find import section
        import_match = re.search(r'(from utils\..*import.*\n)', content)
        if import_match:
            last_import = import_match.end()
            content = (content[:last_import] + 
                      'from utils.db_utils import safe_commit\n' + 
                      content[last_import:])
        else:
            # Add after Flask imports
            flask_import = content.find('from flask import')
            if flask_import != -1:
                end_line = content.find('\n', flask_import)
                content = (content[:end_line + 1] + 
                          'from utils.db_utils import safe_commit\n' + 
                          content[end_line + 1:])
    
    # Replace simple commits
    content = re.sub(
        r'(\s+)(db\.session\.commit\(\))',
        r'\1safe_commit(db, "Database commit failed")',
        content
    )
    
    return content


def add_validators_import(content):
    """
    Add validators import if needed
    """
    if 'from utils.validators import' not in content:
        # Find import section
        db_utils_import = content.find('from utils.db_utils')
        if db_utils_import != -1:
            end_line = content.find('\n', db_utils_import)
            content = (content[:end_line + 1] + 
                      'from utils.validators import Validator, validate_form_data\n' + 
                      content[end_line + 1:])
    
    return content


def process_file(file_path):
    """Process a single file"""
    print(f"📝 {file_path.name}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Apply fixes
        content = wrap_commits_intelligently(content)
        content = add_validators_import(content)
        
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Count replacements
            commit_count = original.count('db.session.commit()')
            safe_commit_count = content.count('safe_commit(db')
            
            print(f"  ✅ Replaced {commit_count} commits")
            return commit_count
        else:
            print(f"  ⏭️  Already fixed")
            return 0
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return 0


def main():
    base_dir = Path(__file__).parent.parent
    
    files = [
        'candidate_panel/app.py',
        'admin_panel/app.py',
        'bot_engine/telegram_bot.py',
        'candidate_panel/benchmark_utils.py',
        'admin_panel/routes_plan_release.py',
        'admin_panel/routes_data_export.py',
        'security/security_utils.py',
    ]
    
    print("="*60)
    print("🔒 Safe Commit Wrapper")
    print("="*60)
    print()
    
    total_commits = 0
    
    for file_rel in files:
        file_path = base_dir / file_rel
        if file_path.exists():
            count = process_file(file_path)
            total_commits += count
    
    print()
    print("="*60)
    print(f"✅ Wrapped {total_commits} commits with safe_commit()")
    print("="*60)


if __name__ == '__main__':
    main()
