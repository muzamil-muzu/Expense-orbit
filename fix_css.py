import glob
import re
import os

for filepath in glob.glob('templates/*.html'):
    if 'base.html' in filepath or 'login.html' in filepath or 'register.html' in filepath:
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Remove all instances of linking style.css in child templates
    new_content = re.sub(r'<link rel="stylesheet" href="\{\{ url_for\(\'static\', filename=\'style\.css\'\) \}\}">\n?', '', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
