#!/usr/bin/env python3
"""
Force clear cache by removing cache entries from smartgov_bot.py
"""

import re

def clear_cache_in_file():
    file_path = "smartgov_bot.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace cache declarations to force clear
    content = re.sub(r'LANGUAGE_CACHE = \{.*?\}', 'LANGUAGE_CACHE = {}  # FORCE CLEARED', content)
    content = re.sub(r'INTENT_CACHE = \{.*?\}', 'INTENT_CACHE = {}  # FORCE CLEARED', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Cache declarations force cleared in smartgov_bot.py")

if __name__ == "__main__":
    clear_cache_in_file() 