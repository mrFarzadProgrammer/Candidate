"""
Add Persian-to-English number converter script to all HTML files
"""
import os
import re

# Script tag to add
script_tag = '    <script src="{{ url_for(\'static\', filename=\'js/persian-to-english-numbers.js\') }}"></script>\n'

# Base directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates_dir = os.path.join(base_dir, 'templates')

def process_html_file(filepath):
    """Add script tag to HTML file if not already present"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if script already exists
        if 'persian-to-english-numbers.js' in content:
            print(f"  ⏭️  Already has script: {os.path.basename(filepath)}")
            return False
        
        # Find </head> tag and add script before it
        if '</head>' in content:
            content = content.replace('</head>', script_tag + '</head>')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✅ Added script to: {os.path.basename(filepath)}")
            return True
        else:
            print(f"  ⚠️  No </head> tag found: {os.path.basename(filepath)}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error processing {filepath}: {e}")
        return False

def main():
    """Process all HTML files"""
    print("🔄 Adding Persian-to-English number converter to all HTML files...")
    print()
    
    updated = 0
    skipped = 0
    
    # Walk through templates directory
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                if process_html_file(filepath):
                    updated += 1
                else:
                    skipped += 1
    
    print()
    print(f"📊 Summary:")
    print(f"  ✅ Updated: {updated} files")
    print(f"  ⏭️  Skipped: {skipped} files")
    print()
    print("✨ Done!")

if __name__ == '__main__':
    main()
