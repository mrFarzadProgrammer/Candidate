import os
import glob

files = glob.glob('templates/candidate/*.html')

for filepath in files:
    try:
        # Read with cp1256
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Decode
        text = data.decode('cp1256')
        
        # Write as UTF-8 without BOM
        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        
        print(f"✓ Fixed: {os.path.basename(filepath)}")
    except Exception as e:
        print(f"✗ Error {os.path.basename(filepath)}: {e}")

print("\nDone!")
